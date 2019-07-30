"""
Pagination helper for use with sqlalchemy
"""
# pylint: disable=R0913
from math import ceil


class PaginationError(Exception):  # pylint: disable=R0903
    """ Exception class for pagniation errors """


class Pagination:
    """ Helper class for sqlalchemy pagination. Inspired by flask-sqlalchemy .paginate
    """

    def __init__(self, query, page, per_page, total, items):
        """

        :param query: the unlimited query object that was used to create this pagination object.
        :param page: the current page number (1 indexed)
        :param per_page: the number of items to be displayed on a page.
        :param total: the total number of items matching the query
        :param items: the items for the current page
        """
        self.query = query
        self.page = page
        self.per_page = per_page
        self.total = total
        self.items = items

    @property
    def pages(self):
        """The total number of pages"""
        if self.per_page == 0 or self.total is None:
            pages = 0
        else:
            pages = int(ceil(self.total / float(self.per_page)))
        return pages

    def prev(self, error_out=False):
        """Returns a :class:`Pagination` object for the previous page.
            :param error_out: error_out boolean to use in paginate object
            :raises AssertionError: if self.query is None
        """
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return paginate(self.query, self.page - 1, self.per_page, error_out)

    @property
    def prev_num(self):
        """Number of the previous page."""
        if not self.has_prev:
            return None
        return self.page - 1

    @property
    def has_prev(self):
        """True if a previous page exists"""
        return self.page > 1

    def next(self, error_out=False):
        """Returns a :class:`Pagination` object for the next page.
            :param error_out: error_out boolean to use in paginate object
            :raises AssertionError: if self.query is None
        """
        assert self.query is not None, 'a query object is required ' \
                                       'for this method to work'
        return paginate(self.query, self.page + 1, self.per_page, error_out)

    @property
    def has_next(self):
        """True if a next page exists."""
        return self.page < self.pages

    @property
    def next_num(self):
        """Number of the next page"""
        if not self.has_next:
            return None
        return self.page + 1


def paginate(query, page=1, per_page=50, error_out=True, max_per_page=None, count=True):
    """ A method to build a pagination object from an unlimited query.
    Inspired by flask-sqlalchemy.

    :param query: the unlimited query object to use to create pagination object
    :param page: the current page number (1 indexed)
    :param per_page: the number of items to be displayed on a page.
    :param error_out: raises PaginationError in odd cases
    :param max_per_page: will use the min of max_per_page and per_page if set
    :param count: if True, will keep track of pagination totals
    :return: Pagination object
    :raises PaginationError when pagination not possible
    """

    if max_per_page is not None:
        per_page = min(per_page, max_per_page)

    if page < 1:
        if error_out:
            raise PaginationError("Not Found")
        page = 1

    if per_page < 0:
        if error_out:
            raise PaginationError("Not Found")
        per_page = 20

    items = query.limit(per_page).offset((page - 1) * per_page).all()

    if not items and page != 1 and error_out:
        raise PaginationError("Not Found")

    if not count:
        total = None
    elif page == 1 and len(items) < per_page:
        total = len(items)
    else:
        total = query.order_by(None).count()

    return Pagination(query, page, per_page, total, items)
