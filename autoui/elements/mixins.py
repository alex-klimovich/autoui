from datetime import timedelta

from autoui.config import Config
from autoui.driver import get_driver
from autoui.elements.abstract import Element
from autoui.helpers import with_wait_element


class _CommonFilling:
    stop_propagation = False

    def _get_names(self):
        """
        Returns names (strings) of class and instance attributes that are instance of ``Element`` class.
        """
        names = set()
        for element_name in self.__class__.__dict__:
            if isinstance(self.__class__.__dict__[element_name], Element):
                names.add(element_name)
        for element_name in self.__dict__:
            if isinstance(self.__dict__[element_name], Element) and element_name not in ('_instance', '_owner'):
                names.add(element_name)
        return names


class Readable(_CommonFilling):
    def get_state(self, stop=False):
        """
        :return:  dict with state data, compatible with ``fill`` method
        :param stop: reserved for stop recursion
        """
        if stop:
            return
        _names = self._get_names()
        state = {}
        for name in _names:
            if self.stop_propagation:
                s = getattr(self, name)().get_state(stop=True)
                if s is not None:
                    state[name] = s
            else:
                state[name] = getattr(self, name)().get_state()
        return state


class Settable(_CommonFilling):
    def fill(self, data, stop=False):
        """
        Recursively fills all elements with data.
        :param data: dictionary to fill with keys as elements names and values as fillable data
        :param stop: reserved for stop recursion
        """
        if stop:
            return
        _names = self._get_names()
        for _k, _v in data.items():
            if _v is not None and _k in _names:
                if self.stop_propagation:
                    getattr(self, _k)().fill(_v, stop=True)
                else:
                    getattr(self, _k)().fill(_v)


class Filling(Readable, Settable):
    """
    Mixin class ``Filling`` for ``Element`` class.
    Those methods should be compatible,
    i.e. data, obtained with ``get_state`` method, should be capable to pass to ``fill`` method without exceptions.
    """


class WaitingElement:
    def __call__(self, timeout=Config.TIMEOUT, poll_frequency=Config.POLL_FREQUENCY):
        self.find(timeout=timeout, poll_frequency=poll_frequency)
        return self

    def find(self, timeout=Config.TIMEOUT, poll_frequency=Config.POLL_FREQUENCY):
        self.wait_until_visible(timeout=timeout, poll_frequency=poll_frequency)


class ScrollingElement:
    def find(self):
        super().find()
        self.scroll_to_element()

    def scroll_to_element(self):
        get_driver().execute_script('return arguments[0].scrollIntoView();', self.web_element)


class WaitingAndScrollingElement(ScrollingElement, WaitingElement):
    # note that class order is reversed when inheritance is used
    # execution order: ScrollingElement.find -- (super) --> WaitingElement.find() --> ... -->
    #                  WaitingElement.wait_until_visible() -- (callback) -->
    #                  ScrollingElement.scroll_to_element()
    pass


class Clicking:
    def click(self, with_js=False):
        if with_js:
            get_driver().execute_script('return argument[0].click()', self.web_element)
        else:
            self.web_element.click()
