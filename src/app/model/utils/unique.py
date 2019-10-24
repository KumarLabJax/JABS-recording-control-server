from src.app.model import SESSION


def _unique(cls, queryfunc, constructor, arg, kw):
    """
    part of a recipe to create model classes that are unique. If a matching
     one already exists in the database it is returned, otherwise one is created
    """
    new = False
    with SESSION.no_autoflush:
        query = SESSION.query(cls)
        query = queryfunc(query, *arg, **kw)
        obj = query.first()
        if not obj:
            new = True
            obj = constructor(*arg, **kw)
            SESSION.add(obj)
    return obj, new


class UniqueMixin(object):
    """
    models models can inherit from this class and implement unique_filter,
    this lets us select an object that matches the filter or create and return
    one if it doesn't already exist.

    """
    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        """ models must implement this method to find a matching object """
        raise NotImplementedError()

    @classmethod
    def as_unique(cls, *arg, **kw):
        """
        method to select or create and return an object using the unique
        Mixin
        """
        return _unique(cls, cls.unique_filter, cls, arg, kw)
