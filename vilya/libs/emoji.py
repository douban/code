#!/usr/bin/env python
# coding=utf-8
import re
import os
from cgi import escape

from mikoto.libs.emoji import *

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
        emoji_img = '<img src="/static/emoji/%s.png" align="absmiddle"/>'
    else:
        emoji_img = '<img src="/static/emoji/%s.png" height="20" width="20" align="absmiddle"/>'
    result = RE_EMOJI.sub(lambda x: emoji_img % x.group().strip(':'), text)
    return result


def all_emojis():
    sub_emoji = 'hub/static/emoji'
    emoji_dir = os.path.join(os.path.curdir, sub_emoji)
    realpath = os.path.dirname(os.path.realpath(__file__))
    curdir = os.path.join(realpath, os.path.pardir, sub_emoji)
    for dir in [emoji_dir, curdir]:
        abs_emoji_dir = os.path.abspath(dir)
        if os.path.isdir(abs_emoji_dir):
            files = os.listdir(abs_emoji_dir)
            if files:
                return [':{}:'.format(fn[:-4]) for fn in files
                        if fn.endswith('.png')]
    return EMOJIS


def url_for_emoji(emoji):
    return '/static/emoji/%s.png' % emoji[1:-1]


RE_EMOJI = re.compile(
    r'(' + '|'.join([re.escape(x) for x in all_emojis()]) + r')')
RE_EMOJI_ONLY = re.compile(
    r'^<p>\s*(' + '|'.join([re.escape(x) for x in all_emojis()]) + r')\s*</p>$')
RE_EMOJI_GROUPS = re.compile(
    '|'.join([re.escape(x) for x in EMOJI_GROUPS.keys()]))
