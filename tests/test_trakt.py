from __future__ import unicode_literals, division, absolute_import

from flexget.plugins.api_trakt import ApiTrakt
from tests import FlexGetBase, use_vcr


lookup_series = ApiTrakt.lookup_series


class TestTraktShowLookup(FlexGetBase):
    __yaml__ = """
        templates:
          global:
            trakt_lookup: yes
            # Access a tvdb field to cause lazy loading to occur
            set:
              afield: "{{tvdb_id}}{{trakt_ep_name}}"
        tasks:
          test_show_lookup:
            mock:
              - title: House
                series_name: House
          test_episode_lookup:
            mock:
              - title: 'House.S01E02.HDTV.XViD-FlexGet'
              - title: 'Doctor.Who.2005.S02E03.PDTV.XViD-FlexGet'
              - title: 'Castle.2009.S03E01'
            series:
              - House
              - Doctor Who 2005
              - Castle (2009)
          test_unknown_series:
            mock:
              - {title: 'Aoeu.Htns.S01E01.htvd'}
            series:
              - Aoeu Htns
          test_date:
            mock:
              - title: the daily show 2012-6-6
            series:
              - the daily show (with jon stewart)
          test_absolute:
            mock:
              - title: naruto 128
            series:
              - naruto
    """

    @use_vcr
    def test_show_lookup(self):
        """trakt: Test Lookup (ONLINE)"""
        self.execute_task('test_show_lookup')
        entry = self.task.find_entry(title='House')
        assert entry['trakt_show_id'] == 1399, \
            'Trakt_ID should be 1339 is %s for %s' % (entry['trakt_series_id'], entry['series_name'])
        assert entry['trakt_series_status'] == 'ended', 'Series status should "ended". Got %s' \
                                                        % (entry['trakt_series_status'])

    @use_vcr
    def test_episode_lookup(self):
        """trakt: Test Lookup (ONLINE)"""
        self.execute_task('test_episode_lookup')
        entry = self.task.find_entry(title='House.S01E02.HDTV.XViD-FlexGet')
        assert entry['trakt_ep_name'] == 'Paternity', \
            '%s trakt_ep_name should be Paternity' % entry['title']
        assert entry['trakt_series_status'] == 'ended', \
            'runtime for %s is %s, should be "ended"' % (entry['title'], entry['trakt_series_status'])
        assert entry['afield'] == '73255Paternity', 'afield was not set correctly'
        assert self.task.find_entry(trakt_ep_name='School Reunion'), \
            'Failed trakt lookup Doctor Who 2005 S02E03'
        entry = self.task.find_entry(title='Castle.2009.S03E01')
        assert entry['trakt_show_id'] == 1410, 'Year in series title should look up as year'

    @use_vcr
    def test_unknown_series(self):
        # Test an unknown series does not cause any exceptions
        self.execute_task('test_unknown_series')
        # Make sure it didn't make a false match
        entry = self.task.find_entry('accepted', title='Aoeu.Htns.S01E01.htvd')
        assert entry.get('trakt_show_id') is None, 'should not have populated trakt data'

    @use_vcr
    def test_date(self):
        self.execute_task('test_date')
        entry = self.task.find_entry(title='the daily show 2012-6-6')
        assert entry.get('trakt_show_id') == 2211, 'should have populated trakt show data'
        assert entry.get('trakt_episode_id') is None, 'should not have populated trakt episode data'


    @use_vcr
    def test_absolute(self):
        self.execute_task('test_absolute')
        entry = self.task.find_entry(title='naruto 128')
        assert entry.get('trakt_show_id') == 46003, 'should have populated trakt show data'
        assert entry.get('trakt_episode_id') is None, 'should not have populated trakt episode data'


class TestTraktList(FlexGetBase):
    __yaml__ = """
        tasks:
          test_trakt_movies:
            trakt_list:
              username: flexgettest
              list: watchlist
              type: movies
    """

    @use_vcr
    def test_trakt_movies(self):
        self.execute_task('test_trakt_movies')
        assert len(self.task.entries) == 1
        entry = self.task.entries[0]
        assert entry['title'] == '12 Angry Men (1957)'
        assert entry['movie_name'] == '12 Angry Men'
        assert entry['movie_year'] == 1957
        assert entry['imdb_id'] == 'tt0050083'


class TestTraktMovieLookup(FlexGetBase):
    __yaml__ = """
        templates:
          global:
            trakt_lookup: yes
        tasks:
          test_lookup_sources:
            mock:
            - title: trakt id
              trakt_movie_id: 481
            - title: tmdb id
              tmdb_id: 603
            - title: imdb id
              imdb_id: tt0133093
            - title: slug
              trakt_movie_slug: the-matrix-1999
            - title: movie_name and movie_year
              movie_name: The Matrix
              movie_year: 1999
            - title: The Matrix (1999)
    """

    @use_vcr
    def test_lookup_sources(self):
        self.execute_task('test_lookup_sources')
        for e in self.task.all_entries:
            assert e['movie_name'] == 'The Matrix', 'looking up based on %s failed' % e['title']
