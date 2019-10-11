# Natural Language Toolkit: Collections
#
# Copyright (C) 2001-2020 NLTK Project
# Author: Steven Bird <stevenbird1@gmail.com>
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT

import bisect
from itertools import islice, chain
from functools import total_ordering

# this unused import is for python 2.7
from collections import defaultdict, deque, Counter

from six import text_type

from nltk.internals import slice_bounds, raise_unorderable_types


##########################################################################
# Ordered Dictionary
##########################################################################


class OrderedDict(dict):
    def __init__(self, data=None, **kwargs):
        self._keys = self.keys(data, kwargs.get("keys"))
        self._default_factory = kwargs.get("default_factory")
        if data is None:
            dict.__init__(self)
        else:
            dict.__init__(self, data)

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self._keys.remove(key)

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)

    def __iter__(self):
        return (key for key in self.keys())

    def __missing__(self, key):
        if not self._default_factory and key not in self._keys:
            raise KeyError()
        return self._default_factory()

    def __setitem__(self, key, item):
        dict.__setitem__(self, key, item)
        if key not in self._keys:
            self._keys.append(key)

    def clear(self):
        dict.clear(self)
        self._keys.clear()

    def copy(self):
        d = dict.copy(self)
        d._keys = self._keys
        return d

    def items(self):
        # returns iterator under python 3 and list under python 2
        return zip(self.keys(), self.values())

    def keys(self, data=None, keys=None):
        if data:
            if keys:
                assert isinstance(keys, list)
                assert len(data) == len(keys)
                return keys
            else:
                assert (
                    isinstance(data, dict)
                    or isinstance(data, OrderedDict)
                    or isinstance(data, list)
                )
                if isinstance(data, dict) or isinstance(data, OrderedDict):
                    return data.keys()
                elif isinstance(data, list):
                    return [key for (key, value) in data]
        elif "_keys" in self.__dict__:
            return self._keys
        else:
            return []

    def popitem(self):
        if not self._keys:
            raise KeyError()

        key = self._keys.pop()
        value = self[key]
        del self[key]
        return (key, value)

    def setdefault(self, key, failobj=None):
        dict.setdefault(self, key, failobj)
        if key not in self._keys:
            self._keys.append(key)

    def update(self, data):
        dict.update(self, data)
        for key in self.keys(data):
            if key not in self._keys:
                self._keys.append(key)

    def values(self):
        # returns iterator under python 3
        return map(self.get, self._keys)


######################################################################
# Lazy Sequences
######################################################################


@total_ordering
class AbstractLazySequence(object):
    """一个抽象基类。
    对于只读序列来说，序列值都要根据需要完成计算。
    懒惰序列扮演了像元素一样的角色：所以支持索引、
    切片和迭代操作；但不能被修改。

    在 NLTK 中大部分共同采用了懒惰序列模式。这是
    针对文集视图对象，因为文集视图对象提供访问一个
    文集的内容，而不是把整个文集都加载到内存中，而
    根据需要从硬盘加载文集中的内容。

    这里没有定义修改一个懒惰序列中的可变元素。在特殊
    情况中，修改元素也许不无法获得永远存储效果，根据
    就是何时何地懒惰序列缓存了元素的值，或者从草稿中
    进行了重建工作。

    抽象基类的子类要覆写 2 个方法： ``__len__()``
    和 ``iterate_from()`` 方法。

    常作为建立一个文集视图对象时使用的类的父类。
    """

    def __len__(self):
        """根据这种文集视图返回文集文件中令牌的数量。
        令牌就是对一段文字进行分词处理。
        """
        raise NotImplementedError("本方法应该覆写在子类中。")

    def iterate_from(self, start):
        """返回一个迭代器对象。
        迭代器对象根据这个文集视图生成文集文件中的令牌。
        如果 ``start>=len(self)`` 的话，令牌起始数是
        ``start`` ，然后这个迭代器对象就不再含有令牌了。
        """
        raise NotImplementedError("本方法应该覆写在子类中。")

    def __getitem__(self, i):
        """支持索引操作的协议部署。
        根据这个文集视图，返回文集文件中第 *i* 个令牌。
        也支持负数和范围索引操作。
        """
        if isinstance(i, slice):
            start, stop = slice_bounds(self, i)
            return LazySubsequence(self, start, stop)
        else:
            # Handle negative indices
            if i < 0:
                i += len(self)
            if i < 0:
                raise IndexError("index out of range")
            # Use iterate_from to extract it.
            try:
                return next(self.iterate_from(i))
            except StopIteration:
                raise IndexError("index out of range")

    def __iter__(self):
        """部署迭代器协议。
        返回一个迭代对象，该对象根据这个文集视图生成文集文件中的令牌。"""
        return self.iterate_from(0)

    def count(self, value):
        """返回包含``value``参数值的次数。"""
        return sum(1 for elt in self if elt == value)

    def index(self, value, start=None, stop=None):
        """返回第一次出现的``value``参数值的索引位值。
        ``value``的值要大于等于``start``的值，并且
        小于``stop``的值。负数值都处理成倒序切片，就是
        从后向前数。"""
        start, stop = slice_bounds(self, slice(start, stop))
        for i, elt in enumerate(islice(self, start, stop)):
            if elt == value:
                return i + start
        raise ValueError("index(x): x not in list")

    def __contains__(self, value):
        """如果列表中含有``value``值，就返回``True``"""
        return bool(self.count(value))

    def __add__(self, other):
        """返回串联结果，即支持``self + other``操作。"""
        return LazyConcatenation([self, other])

    def __radd__(self, other):
        """返回串联结果，支持``other + self``操作。"""
        return LazyConcatenation([other, self])

    def __mul__(self, count):
        """返回串联结果，支持``self * count``操作。"""
        return LazyConcatenation([self] * count)

    def __rmul__(self, count):
        """返回串联结果，支持``count * self``操作。"""
        return LazyConcatenation([self] * count)

    _MAX_REPR_SIZE = 60

    def __repr__(self):
        """
        返回本文集视图的原始字符串形式，
        类似一种列表形式；但如果内容超过60个字符的话，
        会用缩短显示内容加上省略号形式表现。
        """
        pieces = []
        length = 5
        for elt in self:
            pieces.append(repr(elt))
            length += len(pieces[-1]) + 2
            if length > self._MAX_REPR_SIZE and len(pieces) > 2:
                return "[%s, ...]" % text_type(", ").join(pieces[:-1])
        return "[%s]" % text_type(", ").join(pieces)

    def __eq__(self, other):
        return type(self) == type(other) and list(self) == list(other)

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if type(other) != type(self):
            raise_unorderable_types("<", self, other)
        return list(self) < list(other)

    def __hash__(self):
        """
        :raise ValueError: 文集视图对象都是非哈希化的。
        """
        raise ValueError("%s objects are unhashable" % self.__class__.__name__)


class LazySubsequence(AbstractLazySequence):
    """一个懒惰序列的实例化子类。
    通过切片一个懒惰序列产生一个子序列对象。
    这个类的实例保留了源序列的一个参考对象，
    并且生成的值是通过查询源序列得来的。
    """

    MIN_SIZE = 100
    """
    The minimum size for which lazy slices should be created.  If
    ``LazySubsequence()`` is called with a subsequence that is
    shorter than ``MIN_SIZE``, then a tuple will be returned instead.
    """

    def __new__(cls, source, start, stop):
        """指导构造器行为的特殊方法。
        从给出的序列建立一个新切片。
        其中 ``start`` 和 ``stop`` 参数是绝对索引位值，
        例如，不应该是负数（不能从后向前切片），
        不能大于 ``source`` 值的长度。

        :Example:
        
        >>> import nltk
        >>> from nltk.corpus.reader.util import *
        >>> f1 = nltk.data.find('corpora/inaugural/README')
        >>> c1 = StreamBackedCorpusView(f1, read_whitespace_block, encoding='utf-8')
        >>> ls = nltk.collections.LazySubsequence(c1, 1, 3)
        >>> ls
        ['Inaugural', 'Address']

        """
        # If the slice is small enough, just use a tuple.
        if stop - start < cls.MIN_SIZE:
            return list(islice(source.iterate_from(start), stop - start))
        else:
            return object.__new__(cls)

    def __init__(self, source, start, stop):
        self._source = source
        self._start = start
        self._stop = stop

    def __len__(self):
        return self._stop - self._start

    def iterate_from(self, start):
        return islice(
            self._source.iterate_from(start + self._start), max(0, len(self) - start)
        )


class LazyConcatenation(AbstractLazySequence):
    """一个懒惰序列的实例化子类。
    懒惰序列形式的组成是通过串联一个列表组成的列表。
    列表的列表也许自身也是懒惰模式。
    就  ``LazyConcatenation`` 来说是负责维护一个索引，
    这个索引是用来保存偏移位值之间的关系追踪，
    二者是串联完的列表中的偏移位值和子列表中的偏移位值之间的关系。
    """

    def __init__(self, list_of_lists):
        self._list = list_of_lists
        self._offsets = [0]

    def __len__(self):
        if len(self._offsets) <= len(self._list):
            for tok in self.iterate_from(self._offsets[-1]):
                pass
        return self._offsets[-1]

    def iterate_from(self, start_index):
        if start_index < self._offsets[-1]:
            sublist_index = bisect.bisect_right(self._offsets, start_index) - 1
        else:
            sublist_index = len(self._offsets) - 1

        index = self._offsets[sublist_index]

        # Construct an iterator over the sublists.
        if isinstance(self._list, AbstractLazySequence):
            sublist_iter = self._list.iterate_from(sublist_index)
        else:
            sublist_iter = islice(self._list, sublist_index, None)

        for sublist in sublist_iter:
            if sublist_index == (len(self._offsets) - 1):
                assert (
                    index + len(sublist) >= self._offsets[-1]
                ), "offests not monotonic increasing!"
                self._offsets.append(index + len(sublist))
            else:
                assert self._offsets[sublist_index + 1] == index + len(
                    sublist
                ), "inconsistent list value (num elts)"

            for value in sublist[max(0, start_index - index) :]:
                yield value

            index += len(sublist)
            sublist_index += 1


class LazyMap(AbstractLazySequence):
    """一个懒惰序列的实例化子类。
    懒惰序列中的元素形式都是通过应用了一个给出的函数作用到
    每个元素上或更多列表上形成的。
    函数是以懒惰方式来被应用，例如，当你从列表读取一个值的时候，
    那么 ``LazyMap`` 会通过给出的函数作用到提供的列表来计算那个要读取的值。
    对于 ``LazyMap`` 类来说，是不可缺少的，因为它是 Python 内置函数
    ``map`` 的懒惰版本。尤其是下面这些表达式都是等价关系（懒惰模式的理解
    可以说是生成器模式，要想得到结果需要用``list()``内置函数来获得。）：

        >>> from nltk.collections import LazyMap
        >>> function = str
        >>> sequence = [1,2,3]
        >>> map(function, sequence) # doctest: +SKIP
        ['1', '2', '3']
        >>> list(LazyMap(function, sequence))
        ['1', '2', '3']

    像 Python ``map`` 内置函数，如果提供的许多列表源不一样长的话，
    那么就会用 ``None`` 值做补位元素值。

    这个 ``LazyMap` 类对节省内存来说是有用的，
    否则每个值都会占用大量内存空间。如果原来的列表值都用懒惰模式建立的话，
    就特别有用，因为会有使用多个文集阅读器来建立多列表参数值的情况。

    典型的用例就是在一个文集上对许多令牌执行特性侦测任务。
    由于众多特性都编码成许多字典数据类型，可能会消耗大量内存，
    而使用一个 ``LazyMap`` 时可以有效地减少内存用量，尤其是在
    训练和运行机器学习分类器时。
    """

    def __init__(self, function, *lists, **config):
        """
        :param function: 作用在 ``lists`` 参数中每个元素上的函数。
            函数应该具备接收多参数的能力，因为 ``lists`` 参数是多参数形式。
        :param lists: 多参数形式，要被处理的列表。
        :param cache_size: 确定本类要使用的缓存大小，默认值是5
        """
        if not lists:
            raise TypeError("LazyMap requires at least two args")

        self._lists = lists
        self._func = function
        self._cache_size = config.get("cache_size", 5)
        self._cache = {} if self._cache_size > 0 else None

        # If you just take bool() of sum() here _all_lazy will be true just
        # in case n >= 1 list is an AbstractLazySequence.  Presumably this
        # isn't what's intended.
        self._all_lazy = sum(
            isinstance(lst, AbstractLazySequence) for lst in lists
        ) == len(lists)

    def iterate_from(self, index):
        # Special case: one lazy sublist
        if len(self._lists) == 1 and self._all_lazy:
            for value in self._lists[0].iterate_from(index):
                yield self._func(value)
            return

        # Special case: one non-lazy sublist
        elif len(self._lists) == 1:
            while True:
                try:
                    yield self._func(self._lists[0][index])
                except IndexError:
                    return
                index += 1

        # Special case: n lazy sublists
        elif self._all_lazy:
            iterators = [lst.iterate_from(index) for lst in self._lists]
            while True:
                elements = []
                for iterator in iterators:
                    try:
                        elements.append(next(iterator))
                    except:  # FIXME: What is this except really catching? StopIteration?
                        elements.append(None)
                if elements == [None] * len(self._lists):
                    return
                yield self._func(*elements)
                index += 1

        # general case
        else:
            while True:
                try:
                    elements = [lst[index] for lst in self._lists]
                except IndexError:
                    elements = [None] * len(self._lists)
                    for i, lst in enumerate(self._lists):
                        try:
                            elements[i] = lst[index]
                        except IndexError:
                            pass
                    if elements == [None] * len(self._lists):
                        return
                yield self._func(*elements)
                index += 1

    def __getitem__(self, index):
        if isinstance(index, slice):
            sliced_lists = [lst[index] for lst in self._lists]
            return LazyMap(self._func, *sliced_lists)
        else:
            # Handle negative indices
            if index < 0:
                index += len(self)
            if index < 0:
                raise IndexError("index out of range")
            # Check the cache
            if self._cache is not None and index in self._cache:
                return self._cache[index]
            # Calculate the value
            try:
                val = next(self.iterate_from(index))
            except StopIteration:
                raise IndexError("index out of range")
            # Update the cache
            if self._cache is not None:
                if len(self._cache) > self._cache_size:
                    self._cache.popitem()  # discard random entry
                self._cache[index] = val
            # Return the value
            return val

    def __len__(self):
        return max(len(lst) for lst in self._lists)


class LazyZip(LazyMap):
    """一个 ``LazyMap`` 的子类。
    一个懒惰序列中的元素都是元组形式，
    把多个列表的对位元素进行配对形成元组组成的列表。
    （理解压缩概念在此处的应用效果就是元组列表形式。）
    列表中的元组都是懒惰模式建立的，例如，当你读取列表中的一项值时，
    那么 ``LazyZip`` 类会通过参数序列值中的对位元素计算那项值。

    对于 ``LazyZip`` 类来说是不可缺少的一种 Python ``zip`` 内置函数
    的懒惰版本。尤其是下面这些表达式都是等价关系：

        >>> from nltk.collections import LazyZip
        >>> sequence1, sequence2 = [1, 2, 3], ['a', 'b', 'c']
        >>> zip(sequence1, sequence2) # doctest: +SKIP
        [(1, 'a'), (2, 'b'), (3, 'c')]
        >>> list(LazyZip(sequence1, sequence2))
        [(1, 'a'), (2, 'b'), (3, 'c')]
        >>> sequences = [sequence1, sequence2, [6,7,8,9]]
        >>> list(zip(*sequences)) == list(LazyZip(*sequences))
        True

    当多参数的众多序列值都特别长时，``LazyZip`` 类对于减少内存消耗是有用的。

    典型用例是在机器学习分类中把黄金标准的众多长序列与预测值组合时，
    或者是为了计算准确率使用的标签任务时。通过懒惰模式建立这些元组
    以及通过避免建立额外的长序列时，内存用量都明显减少。
    """

    def __init__(self, *lists):
        """
        :param lists: 多参数形式，被处理的列表。
        :type lists: 确保能够支持 ``list(list)`` 操作。
        """
        LazyMap.__init__(self, lambda *elts: elts, *lists)

    def iterate_from(self, index):
        iterator = LazyMap.iterate_from(self, index)
        while index < len(self):
            yield next(iterator)
            index += 1
        return

    def __len__(self):
        return min(len(lst) for lst in self._lists)


class LazyEnumerate(LazyZip):
    """一个 ``LazyZip`` 的子类。
    一个懒惰序列中的元素都是元组形式，
    每个元素都包含一个数算情况（从0开始数）并且
    由序列产生一个值。
    对于包含一种含有索引位的列表来说 ``LazyEnumerate`` 类是有用的。
    其中元组项都是懒惰模式建立的，例如，当你从一个列表读取一个值时，
    那么 ``LazyEnumerate`` 类会计算那个值所在的索引位形成一个元组。

    ``LazyEnumerate`` 类是不可缺少的 Python 内置函数 ``enumerate`` 的懒惰版本。
    尤其是下面这些表达式都是等价关系：

        >>> from nltk.collections import LazyEnumerate
        >>> sequence = ['first', 'second', 'third']
        >>> list(enumerate(sequence))
        [(0, 'first'), (1, 'second'), (2, 'third')]
        >>> list(LazyEnumerate(sequence))
        [(0, 'first'), (1, 'second'), (2, 'third')]

    ``LazyEnumerate`` 类在参数序列特别长时对节省内存有用。

    典型用例是获得一个含有索引位的特别长的列表。
    通过懒惰模式建立的这些元组项，以及避免建立过长的序列时，
    内存用量都会足够地减少。
    """

    def __init__(self, lst):
        """
        :param lst: the underlying list
        :type lst: list
        """
        LazyZip.__init__(self, range(len(lst)), lst)


class LazyIteratorList(AbstractLazySequence):
    """一个懒惰序列的实例化子类。
    打包了一个迭代器对象，根据需要加载该对象中的元素，
    并且让这些元素支持索引操作。
    dunder repr 只显示前几项元素内容。

    注意迭代器对象不能使用负数切片操作。

    :Example:
    
    >>> from nltk.collections import LazyIteratorList
    >>> lil = LazyIteratorList(iter(range(100)))
    >>> lil[:10]
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    """

    def __init__(self, it, known_len=None):
        self._it = it
        self._len = known_len
        self._cache = []

    def __len__(self):
        """增加支持索引操作。"""
        if self._len:
            return self._len
        for x in self.iterate_from(len(self._cache)):
            pass
        self._len = len(self._cache)
        return self._len

    def iterate_from(self, start):
        """在提供的列表索引位值上建立一个新的迭代器对象。"""
        while len(self._cache) < start:
            v = next(self._it)
            self._cache.append(v)
        i = start
        while i < len(self._cache):
            yield self._cache[i]
            i += 1
        while True:
            v = next(self._it)
            self._cache.append(v)
            yield v
            i += 1

    def __add__(self, other):
        """支持``self + other``操作。"""
        return type(self)(chain(self, other))

    def __radd__(self, other):
        """支持``other + self``操作。"""
        return type(self)(chain(other, self))


######################################################################
# Trie Implementation
######################################################################
class Trie(dict):
    """为字符串实现一个 Trie 字典树。"""

    LEAF = True

    def __init__(self, strings=None):
        """初始化一个 ``Trie`` 实例对象，该实例是一个 ``dict`` 数据结构。

        如果 ``strings`` 参数提供了值的话，会把字符串进行列表处理后，
        每一个字符作为字典键，字典值是一个字典。
        值字典的键是``True``，值字典的值是``None``。
        否则建立的是一个空字典形式的 Trie 对象。

        俗称刨根问题、追根溯源算法。阅读 `[字典树算法] <https://en.wikipedia.org/wiki/Trie>_`

        :param strings: 字符串经过列表化后把最后一项插入到字典树节点上，默认值是``None``
        :type strings: 要支持 ``list(str)`` 操作。

        """
        super(Trie, self).__init__()
        if strings:
            for string in strings:
                self.insert(string)

    def insert(self, string):
        """把 ``string`` 参数值分解后每个字符插入到字典树节点上的方法。

        :param string: 要插入到字典树上的字符串。
        :type string: ``str``

        :Example:

        >>> from nltk.collections import Trie
        >>> trie = Trie(["abc", "def"])
        >>> expected = {'a': {'b': {'c': {True: None}}}, \
                        'd': {'e': {'f': {True: None}}}}
        >>> trie == expected
        True

        """
        if len(string):
            self[string[0]].insert(string[1:])
        else:
            # mark the string is complete
            self[Trie.LEAF] = None

    def __missing__(self, key):
        self[key] = Trie()
        return self[key]
