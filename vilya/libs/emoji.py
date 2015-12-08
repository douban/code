#!/usr/bin/env python
# coding=utf-8
import re
import os
from cgi import escape

EMOJIS = [
    ':Aquarius:', ':two_women_in_love:', ':bus_stop:', ':speak_no_evil_monkey:',
    ':chicken:', ':heart_eyes:', ':Scorpius:', ':smiley_confused:',
    ':cat_face_with_wry_smile:', ':GAKUEngine:', ':pistol:', ':relieved:',
    ':wink:', ':grimacing:', ':rainbow_solid:', ':blowfish:',
    ':kissing_smiling_eyes:', ':tropical_drink:', ':face_with_medical_mask:',
    ':pill:', ':ruby:', ':cactus:', ':smiley_stuck_out_tongue_winking_eye:',
    ':boar:', ':smile:', ':face_with_tear_of_joy:', ':Cancer:',
    ':couple_in_love:', ':horse:', ':two_men_with_heart:', ':bowtie:',
    ':open_mouth:', ':frog_face:', ':Taurus:', ':octopus:', ':ship:',
    ':shooting_star:', ':face_with_ok_gesture:', ':wolf_face:', ':heart:',
    ':loudly_crying_face:', ':frowning:', ':scuba_diver:', ':love_hotel:',
    ':gentleman_octopus:', ':grinning_cat_face_with_smiling_eyes:',
    ':face_savouring_delicious_food:', ':rainbow:', ':mount_fuji:',
    ':victory_hand:', ':glowing_star:', ':ksroom:', ':beer_mug:', ':sweat:',
    ':hushed:', ':Pisces:', ':Capricorn:', ':stuck_out_tongue_winking_eye:',
    ':tennis_racquet_and_ball:', ':person_frowning:', ':spouting_whale:',
    ':tangerine:', ':person_bowing_deeply:', ':stuck_out_tongue_closed_eyes:',
    ':dog_face:', ':circled_ideograph_secret:', ':Libra:', ':jumping_spider:',
    ':disappointed_face:', ':hamburger:', ':octocat:', ':sleeping:',
    ':crescent_moon:', ':no_one_under_eighteen_symbol:', ':kissing:',
    ':unamused:', ':couple_with_heart:', ':fisted_hand_sign:',
    ':smiling_cat_face_with_heart_shaped_eyes:', ':anguished:', ':groupme:',
    ':expressionless:', ':phone_book:', ':full_moon:', ':bactrian_camel:',
    ':snowboarder:', ':microphone:', ':Gemini:', ':fearful_face:',
    ':pensive_face:', ':jack_o_lantern:', ':Aries:', ':palm_pre3:',
    ':speech_balloon:', ':koala:', ':poop:', ':quoll:', ':kissing_closed_eyes:',
    ':thumbs_up_sign:', ':person_with_folded_hands:', ':puke_finger:',
    ':Giorgio:', ':princess:', ':waxing_gibbous_moon:', ':two_men_in_love:',
    ':happijar:', ':guitar:', ':sun_with_face:', ':RV:', ':cloud:',
    ':grinning:', ':genshin:', ':Sagittarius:',
    ':disappointed_but_relieved_face:', ':paw_prints:', ':rice_ball:',
    ':anchor:', ':smirk:', ':pegasus_black:', ':lgtm:', ':persevering_face:',
    ':elephant:', ':face_with_no_good_gesture:', ':snake:', ':wink2:',
    ':pizza:', ':white_smiling_face:', ':Leo:', ':sunrise_over_mountains:',
    ':monster:', ':relaxed:', ':grin:', ':laughing:', ':car:', ':cake:',
    ':Kagetsuki:', ':ninja:', ':siamese_kitten:', ':weary_face:', ':ghost:',
    ':milky_way:', ':penguin:', ':drunk:', ':crying_cat_face:', ':dancer:',
    ':snail:', ':person_raising_both_hands_in_celebration:', ':smiley:',
    ':penguin_chick:', ':video_game:', ':flushed:', ':shit:', ':worried:',
    ':cyclone:', ':DSLR_click:', ':jumping_spider_red:', ':ocean_dive_view:',
    ':astonished_face:', ':happy_person_raising_one_hand:', ':bgok:',
    ':family:', ':smiley_smile:', ':wheelchair:', ':Happy_FMC:',
    ':smiley_kissing_heart:', ':hatching_chick:', ':hear_no_evil_monkey:',
    ':Virgo:', ':skull:', ':two_women_holding_hands:', ':assault_rifle:',
    ':pouting_face:', ':high_hopes:', ':angry_face:'
]

EMOJIONE = [
    ':2714:', ':2716:', ':274C:', ':274E:', ':2753:', ':2754:', ':2755:',
    ':2757:', ':2764:', ':303D:', ':1F401:', ':1F402:', ':1F403:', ':1F404:',
    ':1F405:', ':1F406:', ':1F407:', ':1F409:', ':1F410:', ':1F411:',
    ':1F412:', ':1F413:', ':1F414:', ':1F415:', ':1F417:', ':1F418:',
    ':1F419:', ':1F420:', ':1F421:', ':1F422:', ':1F423:', ':1F425:',
    ':1F426:', ':1F427:', ':1F428:', ':1F429:', ':1F430:', ':1F431:',
    ':1F433:', ':1F434:', ':1F435:', ':1F436:', ':1F437:', ':1F438:',
    ':1F439:', ':1F493:', ':1F494:', ':1F495:', ':1F496:', ':1F497:',
    ':1F498:', ':1F499:', ':1F590:', ':1F591:', ':1F592:', ':1F593:',
    ':1F594:', ':1F595:', ':1F596:', ':1F598:', ':1F599:', ':1F59E:',
    ':1F59F:', ':1F600:', ':1F601:', ':1F602:', ':1F604:', ':1F605:',
    ':1F606:', ':1F607:', ':1F608:', ':1F609:', ':1F60A:', ':1F60C:',
    ':1F60D:', ':1F60E:', ':1F60F:', ':1F610:', ':1F611:', ':1F612:',
    ':1F614:', ':1F615:', ':1F616:', ':1F617:', ':1F618:', ':1F619:',
    ':1F61A:', ':1F61C:', ':1F61D:', ':1F61E:', ':1F61F:', ':1F620:',
    ':1F621:', ':1F622:', ':1F624:', ':1F625:', ':1F626:', ':1F627:',
    ':1F628:', ':1F629:', ':1F62A:', ':1F62C:', ':1F62D:', ':1F62E:',
    ':1F62F:', ':1F630:', ':1F631:', ':1F632:', ':1F634:', ':1F635:',
    ':1F636:', ':1F637:', ':1F638:', ':1F639:', ':1F63A:', ':1F63C:',
    ':1F63D:', ':1F63E:', ':1F63F:', ':1F640:', ':1F641:', ':1F642:',
    ':1F646:', ':1F647:', ':1F648:', ':1F649:', ':1F64A:', ':1F64B:',
    ':1F64C:', ':2049:', ':261D:', ':263A:', ':2705:', ':270A:', ':270B:',
    ':270C:', ':270F:', ':2716:', ':274C:', ':274E:', ':2753:', ':2754:',
    ':2755:', ':2757:', ':2764:'
]

TWEMOJI = [
    ':1f400:', ':1f401:', ':1f402:', ':1f403:', ':1f404:', ':1f405:',
    ':1f406:', ':1f407:', ':1f408:', ':1f409:', ':1f410:', ':1f411:',
    ':1f412:', ':1f413:', ':1f414:', ':1f415:', ':1f416:', ':1f417:',
    ':1f418:', ':1f419:', ':1f420:', ':1f421:', ':1f422:', ':1f423:',
    ':1f424:', ':1f425:', ':1f426:', ':1f427:', ':1f428:', ':1f429:',
    ':1f430:', ':1f431:', ':1f432:', ':1f433:', ':1f434:', ':1f435:',
    ':1f436:', ':1f437:', ':1f438:', ':1f439:', ':1f440:', ':1f445:',
    ':1f446:', ':1f447:', ':1f448:', ':1f449:', ':1f450:', ':1f600:',
    ':1f601:', ':1f602:', ':1f603:', ':1f604:', ':1f605:', ':1f606:',
    ':1f607:', ':1f608:', ':1f609:', ':1f60a:', ':1f60b:', ':1f60c:',
    ':1f60d:', ':1f60e:', ':1f60f:', ':1f610:', ':1f611:', ':1f612:',
    ':1f613:', ':1f614:', ':1f615:', ':1f616:', ':1f617:', ':1f618:',
    ':1f619:', ':1f61a:', ':1f61b:', ':1f61c:', ':1f61d:', ':1f61e:',
    ':1f61f:', ':1f620:', ':1f621:', ':1f622:', ':1f623:', ':1f624:',
    ':1f625:', ':1f626:', ':1f627:', ':1f628:', ':1f629:', ':1f62a:',
    ':1f62b:', ':1f62c:', ':1f62d:', ':1f62e:', ':1f62f:', ':1f630:',
    ':1f631:', ':1f632:', ':1f633:', ':1f634:', ':1f635:', ':1f636:',
    ':1f637:', ':1f638:', ':1f639:', ':1f63a:', ':1f63b:', ':1f63c:',
    ':1f63d:', ':1f63e:', ':1f63f:', ':1f640:', ':1f645:', ':1f646:',
    ':1f647:', ':1f648:', ':1f649:', ':1f64a:', ':1f64f:', ':1f680:',
    ':1f681:', ':1f682:'
]

EMOJI_GROUPS = {}


def parse_emoji_groups(text):
    groups = set(RE_EMOJI_GROUPS.findall(text))
    for group in groups:
        group_text = EMOJI_GROUPS[group]
        group_text = group_text.replace(' ', '&nbsp;')
        group_text = group_text.replace('\n', "<br/>")
        text = text.replace(group, group_text)
    return text


def parse_emoji(text, is_escape=True):
    if not text:
        return ''
    if is_escape:
        text = escape(text)
    text = parse_emoji_groups(text)
    if RE_EMOJI_ONLY.match(text.strip()):
        quick_emoji = True
        emoji_img = '<img src="/static/emoji/%s.png" align="absmiddle"/>'
    else:
        quick_emoji = False
        emoji_img = '<img src="/static/emoji/%s.png" height="20" width="20" align="absmiddle"/>'

    def translate_emoji(x):
        text = x.group()
        line_emoji_img = '<img src="/static/emoji/%s.png" height="48" width="48" align="absmiddle"/>'
        if not quick_emoji and RE_EMOJI_LINE.match(text):
            return line_emoji_img % text.strip(':')
        return emoji_img % text.strip(':')

    result = RE_EMOJI.sub(translate_emoji, text)
    return result


def all_emojis():
    curdir = os.path.abspath(os.path.curdir)
    emoji_dir = os.path.join(curdir, 'hub/static/emoji/')
    if os.path.isdir(emoji_dir):
        files = os.listdir(emoji_dir)
    else:
        realpath = os.path.dirname(os.path.realpath(__file__))
        curdir = os.path.join(realpath, os.path.pardir, 'hub/static/emoji')
        curdir = os.path.abspath(curdir)
        if os.path.isdir(curdir):
            files = os.listdir(emoji_dir)
        else:
            return EMOJIS
    if files:
        return [':{}:'.format(fn[:-4]) for fn in files if fn.endswith('.png')]
    else:
        return EMOJIS


def url_for_emoji(emoji):
    return '/static/emoji/%s.png' % emoji[1:-1]


def all_line_emojis():
    return sum([EMOJIONE, TWEMOJI], [])


RE_EMOJI = re.compile(r'(' + '|'.join(
    [re.escape(x) for x in all_emojis()]) + r')')
RE_EMOJI_ONLY = re.compile(r'^<p>\s*(' + '|'.join(
    [re.escape(x) for x in all_emojis()]) + r')\s*</p>$')
RE_EMOJI_GROUPS = re.compile('|'.join(
    [re.escape(x) for x in EMOJI_GROUPS.keys()]))
RE_EMOJI_LINE = re.compile(r'(' + '|'.join(
    [re.escape(x) for x in all_line_emojis()]) + r')')
