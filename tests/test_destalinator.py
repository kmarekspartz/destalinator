# pylint: disable=W0201
from datetime import date, datetime, timedelta
import mock
import os
import unittest

from config import get_config
import destalinator
import slacker
import slackbot


sample_slack_messages = [
    {
        "type": "message",
        "channel": "C2147483705",
        "user": "U2147483697",
        "text": "Human human human.",
        "ts": "1355517523.000005",
        "edited": {
            "user": "U2147483697",
            "ts": "1355517536.000001"
        }
    },
    {
        "type": "message",
        "subtype": "bot_message",
        "text": "Robot robot robot.",
        "ts": "1403051575.000407",
        "user": "U023BEAD1"
    },
    {
        "type": "message",
        "subtype": "channel_name",
        "text": "#stalin has been renamed <C2147483705|khrushchev>",
        "ts": "1403051575.000407",
        "user": "U023BECGF"
    },
    {
        "type": "message",
        "channel": "C2147483705",
        "user": "U2147483697",
        "text": "Contemplating existence.",
        "ts": "1355517523.000005"
    },
    {
        "type": "message",
        "subtype": "bot_message",
        "attachments": [
            {
                "fallback": "Required plain-text summary of the attachment.",
                "color": "#36a64f",
                "pretext": "Optional text that appears above the attachment block",
                "author_name": "Bobby Tables",
                "author_link": "http://flickr.com/bobby/",
                "author_icon": "http://flickr.com/icons/bobby.jpg",
                "title": "Slack API Documentation",
                "title_link": "https://api.slack.com/",
                "text": "Optional text that appears within the attachment",
                "fields": [
                    {
                        "title": "Priority",
                        "value": "High",
                        "short": False
                    }
                ],
                "image_url": "http://my-website.com/path/to/image.jpg",
                "thumb_url": "http://example.com/path/to/thumb.png",
                "footer": "Slack API",
                "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                "ts": 123456789
            }
        ],
        "ts": "1403051575.000407",
        "user": "U023BEAD1"
    }
]

sample_warning_messages = [
    {
        "user": "U023BCDA1",
        "text": "This is a channel warning! Put on your helmets!",
        "username": "bot",
        "bot_id": "B0T8EDVLY",
        "attachments": [{"fallback": "channel_warning", "id": 1}],
        "type": "message",
        "subtype": "bot_message",
        "ts": "1496855882.185855"
    }
]


class MockValidator(object):

    def __init__(self, validator):
        # validator is a function that takes a single argument and returns a bool.
        self.validator = validator

    def __eq__(self, other):
        return bool(self.validator(other))


class SlackerMock(slacker.Slacker):
    def get_users(self):
        pass

    def get_channels(self):
        pass


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorChannelMarkupTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('tests.test_destalinator.SlackerMock')
        self.addCleanup(patcher.stop)
        self.slacker = patcher.start()
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    def test_add_slack_channel_markup(self):
        input_text = "Please find my #general channel reference."
        self.slacker.add_channel_markup.return_value = "<#ABC123|general>"
        self.assertEqual(
            self.destalinator.add_slack_channel_markup(input_text),
            "Please find my <#ABC123|general> channel reference."
        )

    def test_add_slack_channel_markup_multiple(self):
        input_text = "Please find my #general multiple #general channel #general references."
        self.slacker.add_channel_markup.return_value = "<#ABC123|general>"
        self.assertEqual(
            self.destalinator.add_slack_channel_markup(input_text),
            "Please find my <#ABC123|general> multiple <#ABC123|general> channel <#ABC123|general> references."
        )

    def test_add_slack_channel_markup_hyphens(self):
        input_text = "Please find my #channel-with-hyphens references."
        self.slacker.add_channel_markup.return_value = "<#EXA456|channel-with-hyphens>"
        self.assertEqual(
            self.destalinator.add_slack_channel_markup(input_text),
            "Please find my <#EXA456|channel-with-hyphens> references."
        )

    def test_add_slack_channel_markup_ignore_screaming(self):
        input_text = "Please find my #general channel reference and ignore my #HASHTAGSCREAMING thanks."
        self.slacker.add_channel_markup.return_value = "<#ABC123|general>"
        self.assertEqual(
            self.destalinator.add_slack_channel_markup(input_text),
            "Please find my <#ABC123|general> channel reference and ignore my #HASHTAGSCREAMING thanks."
        )


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorChannelMinimumAgeTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('tests.test_destalinator.SlackerMock')
        self.addCleanup(patcher.stop)
        self.slacker = patcher.start()
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    def test_channel_is_old(self):
        self.slacker.get_channel_info.return_value = {'age': 86400 * 60}
        self.assertTrue(self.destalinator.channel_minimum_age("testing", 30))

    def test_channel_is_exactly_expected_age(self):
        self.slacker.get_channel_info.return_value = {'age': 86400 * 30}
        self.assertFalse(self.destalinator.channel_minimum_age("testing", 30))

    def test_channel_is_young(self):
        self.slacker.get_channel_info.return_value = {'age': 86400 * 1}
        self.assertFalse(self.destalinator.channel_minimum_age("testing", 30))


target_archive_date = date.today() + timedelta(days=10)
target_archive_date_string = target_archive_date.isoformat()


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorGetEarliestArchiveDateTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('tests.test_destalinator.SlackerMock')
        self.addCleanup(patcher.stop)
        self.slacker = patcher.start()
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    # TODO: This test (and others) would be redundant with solid testing around config directly.
    @mock.patch.dict(os.environ, {'DESTALINATOR_EARLIEST_ARCHIVE_DATE': target_archive_date_string})
    def test_env_var_name_set_in_config(self):
        self.assertEqual(self.destalinator.get_earliest_archive_date(), target_archive_date)

    @mock.patch.object(get_config(), 'earliest_archive_date', target_archive_date_string)
    def test_archive_date_set_in_config(self):
        self.assertEqual(self.destalinator.get_earliest_archive_date(), target_archive_date)

    @mock.patch.object(get_config(), 'earliest_archive_date_env_varname', None)
    @mock.patch.object(get_config(), 'earliest_archive_date', None)
    def test_falls_back_to_past_date(self):
        self.assertEqual(
            self.destalinator.get_earliest_archive_date(),
            datetime.strptime(destalinator.PAST_DATE_STRING, "%Y-%m-%d").date()
        )


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorGetMessagesTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('tests.test_destalinator.SlackerMock')
        self.addCleanup(patcher.stop)
        self.slacker = patcher.start()
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    def test_with_default_included_subtypes(self):
        self.slacker.get_channelid.return_value = "123456"
        self.slacker.get_messages_in_time_range.return_value = sample_slack_messages
        self.assertEqual(len(self.destalinator.get_messages("general", 30)), len(sample_slack_messages))

    @mock.patch.object(get_config(), 'included_subtypes', [])
    def test_with_empty_included_subtypes(self):
        self.slacker.get_channelid.return_value = "123456"
        self.slacker.get_messages_in_time_range.return_value = sample_slack_messages
        self.assertEqual(
            len(self.destalinator.get_messages("general", 30)),
            sum('subtype' not in m for m in sample_slack_messages)
        )

    @mock.patch.object(get_config(), 'included_subtypes', ['bot_message'])
    def test_with_limited_included_subtypes(self):
        self.slacker.get_channelid.return_value = "123456"
        self.slacker.get_messages_in_time_range.return_value = sample_slack_messages
        self.assertEqual(
            len(self.destalinator.get_messages("general", 30)),
            sum(m.get('subtype', None) in (None, 'bot_message') for m in sample_slack_messages)
        )


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorGetStaleChannelsTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('tests.test_destalinator.SlackerMock')
        self.addCleanup(patcher.stop)
        self.slacker = patcher.start()
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    def test_with_no_stale_channels_but_all_minimum_age_with_default_ignore_users(self):
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        self.slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.get_messages = mock.MagicMock(return_value=sample_slack_messages)
        self.assertEqual(len(self.destalinator.get_stale_channels(30)), 0)

    @mock.patch.object(get_config(), 'ignore_users', [m['user'] for m in sample_slack_messages if m.get('user')])
    def test_with_no_stale_channels_but_all_minimum_age_with_specific_ignore_users(self):
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        self.slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.get_messages = mock.MagicMock(return_value=sample_slack_messages)
        self.assertEqual(len(self.destalinator.get_stale_channels(30)), 2)


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorIgnoreChannelTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('tests.test_destalinator.SlackerMock')
        self.addCleanup(patcher.stop)
        self.slacker = patcher.start()
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    @mock.patch.object(get_config(), 'ignore_channels', ['stalinists'])
    def test_with_explicit_ignore_channel(self):
        self.assertTrue(self.destalinator.ignore_channel('stalinists'))

    @mock.patch.object(get_config(), 'ignore_channel_patterns', ['^stal'])
    def test_with_matching_ignore_channel_pattern(self):
        self.assertTrue(self.destalinator.ignore_channel('stalinists'))

    @mock.patch.object(get_config(), 'ignore_channel_patterns', ['^len'])
    def test_with_non_mathing_ignore_channel_pattern(self):
        self.assertFalse(self.destalinator.ignore_channel('stalinists'))

    @mock.patch.object(get_config(), 'ignore_channel_patterns', ['^len', 'lin', '^st'])
    def test_with_many_matching_ignore_channel_patterns(self):
        self.assertTrue(self.destalinator.ignore_channel('stalinists'))

    @mock.patch.object(get_config(), 'ignore_channels', [])
    @mock.patch.object(get_config(), 'ignore_channel_patterns', [])
    def test_with_empty_ignore_channel_config(self):
        self.assertFalse(self.destalinator.ignore_channel('stalinists'))


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorStaleTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('tests.test_destalinator.SlackerMock')
        self.addCleanup(patcher.stop)
        self.slacker = patcher.start()
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    def test_with_all_sample_messages(self):
        self.slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.get_messages = mock.MagicMock(return_value=sample_slack_messages)
        self.assertFalse(self.destalinator.stale('stalinists', 30))

    @mock.patch.object(get_config(), 'ignore_users', [m['user'] for m in sample_slack_messages if m.get('user')])
    def test_with_all_users_ignored(self):
        self.slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.get_messages = mock.MagicMock(return_value=sample_slack_messages)
        self.assertTrue(self.destalinator.stale('stalinists', 30))

    def test_with_only_a_dolphin_message(self):
        self.slacker.get_channel_info.return_value = {'age': 60 * 86400}
        messages = [
            {
                "type": "message",
                "channel": "C2147483705",
                "user": "U2147483697",
                "text": ":dolphin:",
                "ts": "1355517523.000005"
            }
        ]
        self.destalinator.get_messages = mock.MagicMock(return_value=messages)
        self.assertTrue(self.destalinator.stale('stalinists', 30))

    def test_with_only_an_attachment_message(self):
        self.slacker.get_channel_info.return_value = {'age': 60 * 86400}
        self.destalinator.get_messages = mock.MagicMock(return_value=[m for m in sample_slack_messages if 'attachments' in m])
        self.assertFalse(self.destalinator.stale('stalinists', 30))


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorArchiveTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('tests.test_destalinator.SlackerMock')
        self.addCleanup(patcher.stop)
        self.slacker = patcher.start()
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    @mock.patch.object(get_config(), 'ignore_channels', ['stalinists'])
    def test_skips_ignored_channel(self):
        self.slacker.post_message.return_value = {}
        self.slacker.archive.return_value = {'ok': True}
        self.destalinator.archive("stalinists")
        self.assertFalse(self.slacker.post_message.called)

    def test_announces_closure_with_closure_text(self):
        self.slacker.post_message.return_value = {}
        self.slacker.archive.return_value = {'ok': True}
        self.slacker.get_channel_member_names.return_value = ['sridhar', 'jane']
        self.destalinator.archive("stalinists")
        self.assertIn(
            mock.call('stalinists', mock.ANY, message_type='channel_archive'),
            self.slacker.post_message.mock_calls
        )

    def test_announces_members_at_channel_closing(self):
        self.slacker.post_message.return_value = {}
        self.slacker.archive.return_value = {'ok': True}
        names = ['sridhar', 'jane']
        self.slacker.get_channel_member_names.return_value = names
        self.destalinator.archive("stalinists")
        self.assertIn(
            mock.call('stalinists', MockValidator(lambda s: all(name in s for name in names)), message_type=mock.ANY),
            self.slacker.post_message.mock_calls
        )

    def test_calls_archive_method(self):
        self.slacker.post_message.return_value = {}
        self.slacker.archive.return_value = {'ok': True}
        self.destalinator.archive("stalinists")
        self.slacker.archive.assert_called_once_with('stalinists')


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorSafeArchiveTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('tests.test_destalinator.SlackerMock')
        self.addCleanup(patcher.stop)
        self.slacker = patcher.start()
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    def test_skips_channel_with_only_restricted_users(self):
        self.slacker.post_message.return_value = {}
        self.slacker.archive.return_value = {'ok': True}
        self.slacker.channel_has_only_restricted_members.return_value = True
        self.destalinator.safe_archive("stalinists")
        self.assertFalse(self.slacker.archive.called)

    def test_skips_archiving_if_before_earliest_archive_date(self):
        self.slacker.post_message.return_value = {}
        self.destalinator.archive = mock.MagicMock(return_value=True)
        self.slacker.channel_has_only_restricted_members.return_value = False
        today = date.today()
        self.destalinator.earliest_archive_date = today + timedelta(days=1)
        self.destalinator.safe_archive("stalinists")
        self.assertFalse(self.destalinator.archive.called)

    def test_calls_archive_method(self):
        self.slacker.post_message.return_value = {}
        self.destalinator.archive = mock.MagicMock(return_value=True)
        self.slacker.channel_has_only_restricted_members.return_value = False
        self.destalinator.safe_archive("stalinists")
        self.destalinator.archive.assert_called_once_with('stalinists')


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorSafeArchiveAllTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('tests.test_destalinator.SlackerMock')
        self.addCleanup(patcher.stop)
        self.slacker = patcher.start()
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    def test_calls_stale_once_for_each_channel(self):
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        self.destalinator.stale = mock.MagicMock(return_value=False)
        self.destalinator.safe_archive_all()

        days = self.destalinator.config.archive_threshold

        self.assertEqual(self.destalinator.stale.mock_calls, [mock.call('leninists', days), mock.call('stalinists', days)])

    def test_only_archives_stale_channels(self):
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}

        def fake_stale(channel, days):
            return {'leninists': True, 'stalinists': False}[channel]

        self.destalinator.stale = mock.MagicMock(side_effect=fake_stale)
        self.destalinator.safe_archive = mock.MagicMock()
        self.destalinator.safe_archive_all()
        self.destalinator.safe_archive.assert_called_once_with('leninists')

    @mock.patch.object(get_config(), 'ignore_channels', ['leninists'])
    def test_does_not_archive_ignored_channels(self):
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}

        def fake_stale(channel, days):
            return {'leninists': True, 'stalinists': False}[channel]

        self.destalinator.stale = mock.MagicMock(side_effect=fake_stale)
        self.slacker.channel_has_only_restricted_members.return_value = False
        self.destalinator.earliest_archive_date = date.today()
        self.destalinator.safe_archive_all()
        self.assertFalse(self.slacker.archive.called)


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorWarnPatcherTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('tests.test_destalinator.SlackerMock')
        self.addCleanup(patcher.stop)
        self.slacker = patcher.start()
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    def test_warns_by_posting_message(self):
        self.slacker.channel_has_only_restricted_members.return_value = False
        self.slacker.get_messages_in_time_range.return_value = sample_slack_messages
        self.destalinator.warn("stalinists", 30)
        self.slacker.post_message.assert_called_with("stalinists",
                                                     self.destalinator.warning_text,
                                                     message_type='channel_warning')

    def test_does_not_warn_when_previous_warning_found(self):
        self.slacker.channel_has_only_restricted_members.return_value = False
        self.slacker.get_messages_in_time_range.return_value = [
            {
                "text": self.destalinator.warning_text,
                "user": "ABC123",
                "attachments": [{"fallback": "channel_warning"}]
            }
        ]
        self.destalinator.warn("stalinists", 30)
        self.assertFalse(self.slacker.post_message.called)

    def test_does_not_warn_when_previous_warning_with_changed_text_found(self):
        self.slacker.channel_has_only_restricted_members.return_value = False
        self.slacker.get_messages_in_time_range.return_value = [
            {
                "text": self.destalinator.warning_text + "Some new stuff",
                "user": "ABC123",
                "attachments": [{"fallback": "channel_warning"}]
            }
        ]
        self.destalinator.warn("stalinists", 30)
        self.assertFalse(self.slacker.post_message.called)


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorWarnSlackerMockTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock(token="token")
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    def test_warns_by_posting_message_with_channel_names(self):
        warning_text = self.destalinator.warning_text + " #leninists"
        self.destalinator.warning_text = warning_text
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        self.slacker.channel_has_only_restricted_members = mock.MagicMock(return_value=False)
        self.slacker.get_messages_in_time_range = mock.MagicMock(return_value=sample_slack_messages)
        self.slacker.post_message = mock.MagicMock(return_value={})
        self.destalinator.warn("stalinists", 30)
        self.slacker.post_message.assert_called_with("stalinists",
                                                     self.destalinator.add_slack_channel_markup(warning_text),
                                                     message_type='channel_warning')


@mock.patch.object(get_config(), 'activated', True)
class DestalinatorPostMarkedUpMessageTestCase(unittest.TestCase):
    def setUp(self):
        self.slacker = SlackerMock(token="token")
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    def test_with_a_string_having_a_channel(self):
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        self.slacker.post_message = mock.MagicMock(return_value={})
        self.destalinator.post_marked_up_message('stalinists', "Really great message about #leninists.")
        self.slacker.post_message.assert_called_once_with('stalinists',
                                                          "Really great message about <#C012839|leninists>.")

    def test_with_a_string_having_many_channels(self):
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        self.slacker.post_message = mock.MagicMock(return_value={})
        self.destalinator.post_marked_up_message('stalinists', "Really great message about #leninists and #stalinists.")
        self.slacker.post_message.assert_called_once_with(
            'stalinists',
            "Really great message about <#C012839|leninists> and <#C102843|stalinists>."
        )

    def test_with_a_string_having_no_channels(self):
        self.slacker.channels_by_name = {'leninists': 'C012839', 'stalinists': 'C102843'}
        self.slacker.post_message = mock.MagicMock(return_value={})
        self.destalinator.post_marked_up_message('stalinists', "Really great message.")
        self.slacker.post_message.assert_called_once_with('stalinists', "Really great message.")


@mock.patch.object(get_config(), 'activated', False)
class DestalinatorDeactivatedArchiveTestCase(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch('tests.test_destalinator.SlackerMock')
        self.addCleanup(patcher.stop)
        self.slacker = patcher.start()
        self.slackbot = slackbot.Slackbot(token="token")
        self.destalinator = destalinator.Destalinator(self.slacker, self.slackbot)

    def test_skips_when_destalinator_not_activated(self):
        self.assertFalse(get_config().activated)
        self.slacker.post_message.return_value = {}
        self.destalinator.archive("stalinists")
        self.assertFalse(self.slacker.post_message.called)


if __name__ == '__main__':
    unittest.main()
