from unittest import mock

# Absolute import needed for mocking ;)
from osctiny.base import DataDir
from .base import OscTest


class DataDirTest(OscTest):

    @mock.patch("os.path.isdir", return_value=True)
    @mock.patch("osctiny.base.open", new_callable=mock.mock_open)
    def test_datadir_for_project_1(self, open_mock, isdir_mock):
        # Data dir exists and overwrite=False
        oscdir = DataDir(self.osc, "/some/path", "Some:Project")
        self.assertEqual(open_mock.call_count, 0)
        self.assertEqual(isdir_mock.call_count, 1)

    @mock.patch("os.makedirs")
    @mock.patch("os.path.isdir", return_value=False)
    @mock.patch("osctiny.base.open", create=True, new_callable=mock.mock_open)
    def test_datadir_for_project_2(self, open_mock, isdir_mock, makedirs_mock):
        # Data dir does not exist
        oscdir = DataDir(self.osc, "/some/path", "Some:Project")
        self.assertEqual(open_mock.call_count, 3)
        self.assertEqual(len(open_mock.mock_calls), 12)
        self.assertEqual(isdir_mock.call_count, 1)

    @mock.patch("os.makedirs")
    @mock.patch("os.path.isdir", return_value=True)
    @mock.patch("osctiny.base.open", create=True, new_callable=mock.mock_open)
    def test_datadir_for_project_3(self, open_mock, isdir_mock, makedirs_mock):
        # Data dir exists and overwrite=True
        oscdir = DataDir(self.osc, "/some/path", "Some:Project", overwrite=True)
        self.assertEqual(open_mock.call_count, 3)
        self.assertEqual(len(open_mock.mock_calls), 12)
        self.assertEqual(isdir_mock.call_count, 1)
