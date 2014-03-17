# -*- coding: utf-8 -*-

__all__ = []
__dict__ = []


from vilya.libs.store import (
        OrzField,
        OrzBase,
        store,
        IntegrityError,
        )
from ORZ.klass_init import OrzMeta
from datetime import datetime


class ModelField(OrzField):
    def __init__(self, *args, **kwargs):
        self.auto_now = kwargs.get('auto_now')
        self.auto_now_create = kwargs.get('auto_now_create')
        if kwargs.has_key('auto_now'):
            del kwargs['auto_now']
        if kwargs.has_key('auto_now_create'):
            del kwargs['auto_now_create']
        super(ModelField, self).__init__(*args, **kwargs)

class ModelMeta(OrzMeta):
    def __init__(self, *args, **kwargs):
        if self.__table__: self.__orz_table__ = self.__table__
        super(ModelMeta, self).__init__(*args, **kwargs)
        
        auto_now_fields = []
        auto_now_create_fields = []
        for k, v in self.__dict__.iteritems():
            if isinstance(v, ModelField):
                if v.auto_now:
                    auto_now_fields.append(k)
                elif v.auto_now_create:
                    auto_now_create_fields.append(k)
        self.__auto_now_fields__ = auto_now_fields
        self.__auto_now_create_fields__ = auto_now_create_fields
        

def _transaction(func):
        def _transaction_block(*args, **kwargs):
            if store.in_transaction or store.modified_cursors:
                return func(*args, **kwargs)
            else:
                store.transaction_begin()
                try:
                    ret = func(*args, **kwargs)
                except IntegrityError, e:
                    store.rollback()
                    raise e
                except Exception, e:
                    store.rollback()
                    raise e
                else:
                    store.commit()
                    return ret
        return _transaction_block


class BaseModel(OrzBase):

    __metaclass__ = ModelMeta
    __transaction__ = True
    __table__ = ''

    def __init__(self, *args, **kwargs):
        super(BaseModel, self).__init__(*args, **kwargs)

    @staticmethod
    def transaction(func):
        return _transaction(func)
    
    @classmethod
    @_transaction
    def create(cls, **kwargs):
        fields = cls.__auto_now_fields__ + cls.__auto_now_create_fields__
        if fields:
            now = datetime.now()
            for field in fields:
                kwargs[field] = now
        return super(BaseModel, cls).create(**kwargs)

    @classmethod
    def get(cls, **kwargs):
        ret = cls.objects.gets_by(**kwargs)
        if len(ret):
            return ret[0]

    @classmethod
    def gets(cls, **kwargs):
        return cls.objects.gets_by(**kwargs)

    @classmethod
    def count(cls, **kwargs):
        return cls.objects.count_by(**kwargs)

    @_transaction
    def save(self):
        fields = self.__auto_now_fields__
        if fields:
            now = datetime.now()
            for field in fields:
                setattr(self, field, now)
        return super(BaseModel, self).save()

    def to_dict(self):
        return {}

    def __iter__(self):
        self.to_dict().iteritems()

