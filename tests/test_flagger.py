import unittest
import mock

import flagger
import tests.fixtures as fixtures
import tests.mocks as mocks

from config import get_config


@mock.patch.object(get_config(), 'activated', True)
class FlaggerFlagTest(unittest.TestCase):
    def setUp(self):
        slacker_obj = mocks.mocked_slacker_object(channels_list=fixtures.channels,
                                                  users_list=fixtures.users,
                                                  messages_list=fixtures.messages,
                                                  emoji_list=fixtures.emoji)
        self.slackbot = mocks.mocked_slackbot_object()
        self.flagger = flagger.Flagger(slacker_injected=slacker_obj, slackbot_injected=self.slackbot)

    def test_flag_posts_interesting_messages(self):
        self.flagger.flag()
        self.assertGreater(len(self.slackbot.say.mock_calls), 0)
