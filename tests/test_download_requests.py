import os
import unittest
from unittest.mock import patch

import downloader


VIDEO_URL = 'https://www.youtube.com/watch?v=sRPDkY3O6_0&index=3'


class DownloadRequestTests(unittest.TestCase):
    def test_other_sites_keep_their_request_settings(self):
        options = {}
        downloader._apply_youtube_request_options(options, 'https://www.bilibili.com/video/BV123')
        self.assertNotIn('impersonate', options)

    def test_youtube_analysis_and_download_use_same_network_options(self):
        options = []

        class FakeYDL:
            def __init__(self, opts):
                options.append(opts)
                self.opts = opts

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def extract_info(self, *_args, **_kwargs):
                return {'title': 'Sample', 'formats': []}

            def download(self, _urls):
                with open(os.path.join(os.path.dirname(self.opts['outtmpl']), 'sample.mp4'), 'wb') as out:
                    out.write(b'sample')

        task_id = 'test_request_options'
        downloader.TASKS[task_id] = {'status': 'starting'}
        try:
            with patch.object(downloader.yt_dlp, 'YoutubeDL', FakeYDL), \
                 patch.object(downloader, 'APP_NATIVE', False), \
                 patch.object(downloader, 'log'):
                downloader.analyze(VIDEO_URL)
                downloader._download(task_id, VIDEO_URL, '270+140', 'video')
            self.assertEqual(downloader.TASKS[task_id]['status'], 'done')
            self.assertEqual(str(options[0].get('impersonate')), 'chrome')
            self.assertEqual(options[0].get('impersonate'), options[1].get('impersonate'))
            self.assertIs(options[1].get('skip_unavailable_fragments'), False)
        finally:
            downloader.cleanup_task(task_id)

    def test_http_403_does_not_retry_with_a_different_format_catalog(self):
        options = []

        class FakeYDL:
            def __init__(self, opts):
                options.append(opts)

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def download(self, _urls):
                raise RuntimeError('HTTP Error 403: Forbidden')

        task_id = 'test_403_retry'
        downloader.TASKS[task_id] = {'status': 'starting'}
        with patch.object(downloader.yt_dlp, 'YoutubeDL', FakeYDL), patch.object(downloader, 'log'):
            downloader._download(task_id, VIDEO_URL, '270+140', 'video')
        self.assertEqual(len(options), 1)
        self.assertIn('403', downloader.TASKS.pop(task_id)['error'])
        self.assertIn('重新分析', downloader._friendly_error('Requested format is not available', 'zh'))


if __name__ == '__main__':
    unittest.main()
