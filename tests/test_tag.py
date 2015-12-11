# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.models.tag import TagName, Tag, TAG_TYPE_PROJECT_ISSUE
from tests.base import TestCase


class TestName(TestCase):

    def test_add(self):
        name = "tag"
        author = "test"
        target_type = 2
        target_id = 3
        tag = TagName.add(name, author, target_type, target_id)
        assert tag.name == name
        assert tag.author_id == author
        assert tag.target_type == target_type
        assert tag.target_id == target_id
        tag.delete()

    def test_get(self):
        name = "tag"
        author = "test"
        target_type = 2
        target_id = 3
        newtag = TagName.add(name, author, target_type, target_id)
        tag = TagName.get_by_name_and_target_id(name, target_type, target_id)
        assert tag.id == newtag.id
        assert tag.name == name
        assert tag.author_id == author
        assert tag.target_type == target_type
        assert tag.target_id == target_id

        tag = TagName.get_by_id(newtag.id)
        assert tag.id == newtag.id
        assert tag.name == name
        assert tag.author_id == author
        assert tag.target_type == target_type
        assert tag.target_id == target_id

    def test_delete(self):
        name = "tag"
        author = "test"
        target_type = 2
        target_id = 3
        newtag = TagName.add(name, author, target_type, target_id)
        newtag.delete()
        tag = TagName.get_by_name_and_target_id(name, target_type, target_id)
        assert tag is None

        tag = TagName.get_by_id(newtag.id)
        assert tag is None


class TestTag(TestCase):

    def test_add(self):
        tag = Tag.add(1, 1, 1, 'test', 3)
        assert tag.tag_id == 1
        assert tag.type == 1
        assert tag.type_id == 1
        assert tag.author_id == 'test'
        assert tag.target_id == 3

    def test_get(self):
        tags = Tag.gets()
        for tag in tags:
            tag.delete()
        Tag.add(1, TAG_TYPE_PROJECT_ISSUE, 1, 'test1', 3)
        Tag.add(2, TAG_TYPE_PROJECT_ISSUE, 1, 'test2', 3)
        Tag.add(1, TAG_TYPE_PROJECT_ISSUE, 2, 'test3', 3)

        tag = Tag.get_by_type_id_and_tag_id(TAG_TYPE_PROJECT_ISSUE, 1, 1)
        assert isinstance(tag, Tag)
        assert tag.tag_id == 1
        assert tag.type == TAG_TYPE_PROJECT_ISSUE
        assert tag.type_id == 1
        assert tag.author_id == 'test1'
        assert tag.target_id == 3

        tags = Tag.gets_by_issue_id(1, TAG_TYPE_PROJECT_ISSUE)
        assert all([isinstance(t, Tag) for t in tags])
        assert len(tags) == 2

    def test_delete(self):
        tag1 = Tag.add(1, TAG_TYPE_PROJECT_ISSUE, 1, 'test1', 2)
        tag2 = Tag.add(2, TAG_TYPE_PROJECT_ISSUE, 1, 'test2', 2)
        tag3 = Tag.add(1, TAG_TYPE_PROJECT_ISSUE, 2, 'test3', 2)
        tag2.delete()
        tag = Tag.get_by_type_id_and_tag_id(TAG_TYPE_PROJECT_ISSUE, 1, 2)
        assert tag is None

    def test_get_type_ids_by_names_and_target_id(self):
        name1 = "tag"
        author = "test"
        type = target_type = TAG_TYPE_PROJECT_ISSUE
        target_id = 3
        tag_name1 = TagName.add(name1, author, target_type, target_id)
        assert tag_name1.name == name1

        author_id = 2
        type_id1 = 1
        type_id2 = 2
        type_id3 = 3
        tag1 = Tag.add(tag_name1.id, type, type_id1, author_id, target_id)
        tag2 = Tag.add(tag_name1.id, type, type_id2, author_id, target_id)
        tag3 = Tag.add(tag_name1.id, type, type_id3, author_id, target_id)

        assert tag1.tag_id == tag2.tag_id == tag3.tag_id

        type_ids = Tag.get_type_ids_by_names_and_target_id(
            type, [name1], target_id)

        assert len(type_ids) == 3
        assert type_id1 in type_ids
        assert type_id2 in type_ids
        assert type_id3 in type_ids

        name2 = "tag2"
        tag_name2 = TagName.add(name2, author, target_type, target_id)
        assert tag_name2.name == name2

        type_id4 = 4
        tag3 = Tag.add(tag_name2.id, type, type_id3, author_id, target_id)
        tag4 = Tag.add(tag_name2.id, type, type_id4, author_id, target_id)

        type_ids = Tag.get_type_ids_by_names_and_target_id(
            type, [name1, name2], target_id)

        print type_ids
        assert len(type_ids) == 1
        assert type_id3 in type_ids

    def test_gets_by_target_id(self):
        tags = Tag.gets()
        for tag in tags:
            tag.delete()
        name = "tag"
        author = "test"
        type = target_type = TAG_TYPE_PROJECT_ISSUE
        target_id = 3
        tag_name = TagName.add(name, author, target_type, target_id)
        assert tag_name.name == name

        author_id = 2
        type_id1 = 1
        type_id2 = 2
        type_id3 = 3
        tag1 = Tag.add(tag_name.id, type, type_id1, author_id, target_id)
        tag2 = Tag.add(tag_name.id, type, type_id2, author_id, target_id)
        tag3 = Tag.add(tag_name.id, type, type_id3, author_id, target_id)

        assert tag1.tag_id == tag2.tag_id == tag3.tag_id

        tags = Tag.gets_by_target_id(type, target_id)

        assert len(tags) == 3

        type_ids = [t.type_id for t in tags]
        assert type_id1 in type_ids
        assert type_id2 in type_ids
        assert type_id3 in type_ids

    def test_gets_by_tag_id(self):
        name = "tag"
        author = "test"
        type = target_type = TAG_TYPE_PROJECT_ISSUE
        target_id = 3
        tag_name = TagName.add(name, author, target_type, target_id)
        assert tag_name.name == name

        author_id = 2
        type_id1 = 1
        type_id2 = 2
        type_id3 = 3
        tag1 = Tag.add(tag_name.id, type, type_id1, author_id, target_id)
        tag2 = Tag.add(tag_name.id, type, type_id2, author_id, target_id)
        tag3 = Tag.add(tag_name.id, type, type_id3, author_id, target_id)

        assert tag1.tag_id == tag2.tag_id == tag3.tag_id

        tags = Tag.gets_by_tag_id(tag_name.id)

        assert len(tags) == 3

        type_ids = [t.type_id for t in tags]
        assert type_id1 in type_ids
        assert type_id2 in type_ids
        assert type_id3 in type_ids
