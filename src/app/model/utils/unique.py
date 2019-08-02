from src.app.model import SESSION


def _unique(cls, queryfunc, constructor, arg, kw):
    """
    part of a recipe to create model classes that are unique. If a matching
     one already exists in the database it is returned, otherwise one is created
    """
    with SESSION.no_autoflush:
        q = SESSION.query(cls)
        q = queryfunc(q, *arg, **kw)
        obj = q.first()
        if not obj:
            obj = constructor(*arg, **kw)
            SESSION.add(obj)
    return obj


class UniqueMixin(object):
    """
    models models can inherit from this class and implement unique_filter,
    this lets us select an object that matches the filter or create and return
    one if it doesn't already exist.

    this is used for the Factor and CellLine which are basically lists of
    controlled vocabulary terms
    """
    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def as_unique(cls, *arg, **kw):
        return _unique(
                    cls,
                    cls.unique_filter,
                    cls,
                    arg, kw
               )
