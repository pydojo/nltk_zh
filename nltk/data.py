# Natural Language Toolkit: Utility functions
#
# Copyright (C) 2001-2020 NLTK Project
# Author: Edward Loper <edloper@gmail.com>
# URL: <http://nltk.org/>
# For license information, see LICENSE.TXT

"""
本模块中的函数是用来找到和加载 NLTK 资源文件用的，
例如，文集、语法、和保存的处理对象。
资源文件都使用 URLs 来进行识别，例如， ``nltk:corpora/abc/rural.txt`` 
或者 ``http://nltk.org/sample/toy.cfg`` 来作为资源文件地址。
如下 URL 协议都是支持的：

  - ``file:path``: 描述一个**文件路径**。
    即可以是相对路径，也可以是绝对路径。

  - ``http://host/path``: 描述存储在网络服务器上的**文件网址** 路径。

  - ``nltk:path``: 描述一个存储在 ``nltk_data/`` 目录中的**文件路径**。
    NLTK 会搜索这个目录里的文件，要描述成 ``nltk.data.path`` 形式。

如果以上3个协议都没有描述，默认采用 ``nltk:`` 协议。

本模块提供的功能是用来访问资源文件，
根据给出的资源 URL：使用 ``load()`` 函数加载资源，然后把资源放到资源缓存中；
使用 ``retrieve()`` 函数把提供的资源复制到一个本地文件里。
"""

import functools
import textwrap
import io
import os
import re
import sys
import zipfile
import codecs

from abc import ABCMeta, abstractmethod
from gzip import GzipFile, WRITE as GZ_WRITE

from six import add_metaclass
from six import string_types, text_type
from six.moves.urllib.request import urlopen, url2pathname

try:
    import cPickle as pickle
except ImportError:
    import pickle

try:  # Python 3.
    textwrap_indent = functools.partial(textwrap.indent, prefix="  ")
except AttributeError:  # Python 2; indent() not available for Python2.
    textwrap_fill = functools.partial(
        textwrap.fill,
        initial_indent="  ",
        subsequent_indent="  ",
        replace_whitespace=False,
    )

    def textwrap_indent(text):
        return "\n".join(textwrap_fill(line) for line in text.splitlines())


try:
    from zlib import Z_SYNC_FLUSH as FLUSH
except ImportError:
    from zlib import Z_FINISH as FLUSH

# this import should be more specific:
import nltk
from nltk.compat import py3_data, add_py3_data, BytesIO

######################################################################
# Search Path
######################################################################

path = []
"""A list of directories where the NLTK data package might reside.
   These directories will be checked in order when looking for a
   resource in the data package.  Note that this allows users to
   substitute in their own versions of resources, if they have them
   (e.g., in their home directory under ~/nltk_data)."""

# User-specified locations:
_paths_from_env = os.environ.get("NLTK_DATA", str("")).split(os.pathsep)
path += [d for d in _paths_from_env if d]
if "APPENGINE_RUNTIME" not in os.environ and os.path.expanduser("~/") != "~/":
    path.append(os.path.expanduser(str("~/nltk_data")))

if sys.platform.startswith("win"):
    # Common locations on Windows:
    path += [
        os.path.join(sys.prefix, str("nltk_data")),
        os.path.join(sys.prefix, str("share"), str("nltk_data")),
        os.path.join(sys.prefix, str("lib"), str("nltk_data")),
        os.path.join(os.environ.get(str("APPDATA"), str("C:\\")), str("nltk_data")),
        str(r"C:\nltk_data"),
        str(r"D:\nltk_data"),
        str(r"E:\nltk_data"),
    ]
else:
    # Common locations on UNIX & OS X:
    path += [
        os.path.join(sys.prefix, str("nltk_data")),
        os.path.join(sys.prefix, str("share"), str("nltk_data")),
        os.path.join(sys.prefix, str("lib"), str("nltk_data")),
        str("/usr/share/nltk_data"),
        str("/usr/local/share/nltk_data"),
        str("/usr/lib/nltk_data"),
        str("/usr/local/lib/nltk_data"),
    ]


######################################################################
# Util Functions
######################################################################


def gzip_open_unicode(
    filename,
    mode="rb",
    compresslevel=9,
    encoding="utf-8",
    fileobj=None,
    errors=None,
    newline=None,
):
    if fileobj is None:
        fileobj = GzipFile(filename, mode, compresslevel, fileobj)
    return io.TextIOWrapper(fileobj, encoding, errors, newline)


def split_resource_url(resource_url):
    """分解资源地址的函数。
    把一个资源地址分解成 "<protocol>:<path>" 形式。

    >>> windows = sys.platform.startswith('win')
    >>> split_resource_url('nltk:home/nltk')
    ('nltk', 'home/nltk')
    >>> split_resource_url('nltk:/home/nltk')
    ('nltk', '/home/nltk')
    >>> split_resource_url('file:/home/nltk')
    ('file', '/home/nltk')
    >>> split_resource_url('file:///home/nltk')
    ('file', '/home/nltk')
    >>> split_resource_url('file:///C:/home/nltk')
    ('file', '/C:/home/nltk')
    """
    protocol, path_ = resource_url.split(":", 1)
    if protocol == "nltk":
        pass
    elif protocol == "file":
        if path_.startswith("/"):
            path_ = "/" + path_.lstrip("/")
    else:
        path_ = re.sub(r"^/{0,2}", "", path_)
    return protocol, path_


def normalize_resource_url(resource_url):
    r"""
    确保一个资源 url 正常。

    >>> windows = sys.platform.startswith('win')
    >>> os.path.normpath(split_resource_url(normalize_resource_url('file:grammar.fcfg'))[1]) == \
    ... ('\\' if windows else '') + os.path.abspath(os.path.join(os.curdir, 'grammar.fcfg'))
    True
    >>> not windows or normalize_resource_url('file:C:/dir/file') == 'file:///C:/dir/file'
    True
    >>> not windows or normalize_resource_url('file:C:\\dir\\file') == 'file:///C:/dir/file'
    True
    >>> not windows or normalize_resource_url('file:C:\\dir/file') == 'file:///C:/dir/file'
    True
    >>> not windows or normalize_resource_url('file://C:/dir/file') == 'file:///C:/dir/file'
    True
    >>> not windows or normalize_resource_url('file:////C:/dir/file') == 'file:///C:/dir/file'
    True
    >>> not windows or normalize_resource_url('nltk:C:/dir/file') == 'file:///C:/dir/file'
    True
    >>> not windows or normalize_resource_url('nltk:C:\\dir\\file') == 'file:///C:/dir/file'
    True
    >>> windows or normalize_resource_url('file:/dir/file/toy.cfg') == 'file:///dir/file/toy.cfg'
    True
    >>> normalize_resource_url('nltk:home/nltk')
    'nltk:home/nltk'
    >>> windows or normalize_resource_url('nltk:/home/nltk') == 'file:///home/nltk'
    True
    >>> normalize_resource_url('http://example.com/dir/file')
    'http://example.com/dir/file'
    >>> normalize_resource_url('dir/file')
    'nltk:dir/file'

    """
    try:
        protocol, name = split_resource_url(resource_url)
    except ValueError:
        # the resource url has no protocol, use the nltk protocol by default
        protocol = "nltk"
        name = resource_url
    # use file protocol if the path is an absolute path
    if protocol == "nltk" and os.path.isabs(name):
        protocol = "file://"
        name = normalize_resource_name(name, False, None)
    elif protocol == "file":
        protocol = "file://"
        # name is absolute
        name = normalize_resource_name(name, False, None)
    elif protocol == "nltk":
        protocol = "nltk:"
        name = normalize_resource_name(name, True)
    else:
        # handled by urllib
        protocol += "://"
    return "".join([protocol, name])


def normalize_resource_name(resource_name, allow_relative=True, relative_path=None):
    """
    :type resource_name: str 或 unicode 类型的字符串。
    :param resource_name: 要寻找的资源名。
        资源名都要是 posix-style 相对路径形式，例如 ``corpora/brown``。
        目录名会自动转换成适合操作系统的路径分隔符。
        目录名的斜杠字符都受到保护。

    >>> windows = sys.platform.startswith('win')
    >>> normalize_resource_name('.', True)
    './'
    >>> normalize_resource_name('./', True)
    './'
    >>> windows or normalize_resource_name('dir/file', False, '/') == '/dir/file'
    True
    >>> not windows or normalize_resource_name('C:/file', False, '/') == '/C:/file'
    True
    >>> windows or normalize_resource_name('/dir/file', False, '/') == '/dir/file'
    True
    >>> windows or normalize_resource_name('../dir/file', False, '/') == '/dir/file'
    True
    >>> not windows or normalize_resource_name('/dir/file', True, '/') == 'dir/file'
    True
    >>> windows or normalize_resource_name('/dir/file', True, '/') == '/dir/file'
    True
    """
    is_dir = bool(re.search(r"[\\/.]$", resource_name)) or resource_name.endswith(
        os.path.sep
    )
    if sys.platform.startswith("win"):
        resource_name = resource_name.lstrip("/")
    else:
        resource_name = re.sub(r"^/+", "/", resource_name)
    if allow_relative:
        resource_name = os.path.normpath(resource_name)
    else:
        if relative_path is None:
            relative_path = os.curdir
        resource_name = os.path.abspath(os.path.join(relative_path, resource_name))
    resource_name = resource_name.replace("\\", "/").replace(os.path.sep, "/")
    if sys.platform.startswith("win") and os.path.isabs(resource_name):
        resource_name = "/" + resource_name
    if is_dir and not resource_name.endswith("/"):
        resource_name += "/"
    return resource_name


######################################################################
# Path Pointers
######################################################################


@add_metaclass(ABCMeta)
class PathPointer(object):
    """一个抽象元类。
    为了路径指向，NLTK 的数据包会使用这个抽象元类来识别具体的路径。
    它有两个子类：
    ``FileSystemPathPointer`` 子类是通过给出的一个绝对路径来
    识别一个可以直接访问的文件。
    ``ZipFilePathPointer`` 子类是识别放在压缩文件里的一个文件，
    通过读取压缩文件来访问里面的文件。
    """

    @abstractmethod
    def open(self, encoding=None):
        """一个抽象类的方法。
        返回可以查询操作的只读流数据，
        流数据可以用来读取文件的内容，
        这个文件是通过路径指针来识别的。

        :raise IOError: 如果路径没有用指针来描述的话，
            就没有一个可读取的文件。
        """

    @abstractmethod
    def file_size(self):
        """一个抽象类的方法。
        返回指向的文件大小（单位是字节），文件要通过路径指针提前描述。

        :raise IOError: 如果没有用路径指针描述不会有课读取的文件。
        """

    @abstractmethod
    def join(self, fileid):
        """一个抽象类的方法。
        返回一个新的路径指针，新指针的起始位置是从本指针识别的路径开始，
        后面跟着给出的 ``fileid`` 参数值的相对路径。
        ``fileid`` 路径的成份应该用斜杠来分隔，会把 ``/`` 视为文件系统
        路径的分隔符。
        """


class FileSystemPathPointer(PathPointer, text_type):
    """一个文件系统路径指针类。
    文件系统路径指针通过给出的绝对路径来识别可以直接访问的文件。
    """

    @py3_data
    def __init__(self, _path):
        """
        为给出的绝对路径建立一个新的路径指针实例。

        :raise IOError: 如果提供的路径不存在。
        """

        _path = os.path.abspath(_path)
        if not os.path.exists(_path):
            raise IOError("No such file or directory: %r" % _path)
        self._path = _path

        # There's no need to call str.__init__(), since it's a no-op;
        # str does all of its setup work in __new__.

    @property
    def path(self):
        """本路径指针实例识别的绝对路径。"""
        return self._path

    def open(self, encoding=None):
        stream = open(self._path, "rb")
        if encoding is not None:
            stream = SeekableUnicodeStreamReader(stream, encoding)
        return stream

    def file_size(self):
        return os.stat(self._path).st_size

    def join(self, fileid):
        _path = os.path.join(self._path, fileid)
        return FileSystemPathPointer(_path)

    def __repr__(self):
        # This should be a byte string under Python 2.x;
        # we don't want transliteration here so
        # @python_2_unicode_compatible is not used.
        return str("FileSystemPathPointer(%r)" % self._path)

    def __str__(self):
        return self._path


class BufferedGzipFile(GzipFile):
    """
    一个 ``GzipFile`` 子类，用来调用 ``read()`` 和 ``write()`` 读写缓存。
    本类的实例能够更快地读写来自压缩文件的数据，所以会更多地消耗内存。

    默认的缓存大小是2MB。

    对于加载大型压缩过的腌制对象来说，``BufferedGzipFile`` 类是有用的，
    对于写入大型含有编码的特性文件来说也是有用的，
    典型用例是针对机器学习的分类器训练。
    """

    MB = 2 ** 20
    SIZE = 2 * MB

    @py3_data
    def __init__(
        self, filename=None, mode=None, compresslevel=9, fileobj=None, **kwargs
    ):
        """
        返回一个缓存过的压缩文件对象。

        :param filename: 一个文件系统路径。
        :type filename: str
        :param mode: 文件的操作模式 'r', 'rb', 'a', 'ab',
            'w', or 'wb' 中的任何一种。
        :type mode: str
        :param compresslevel: 压缩等级，从1到9的整数分别控制压缩级别；
            值是 1 时最快压缩率最小，值是 9 时最慢压缩率最大。默认值是9。
        :type compresslevel: int
        :param fileobj: 一种字节流数据，从 BytesIO 读取，不读取文件。
        :type fileobj: BytesIO
        :param size: 字节数量，调用 read() 和 write() 时的缓存大小。
        :type size: int
        :rtype: BufferedGzipFile
        """
        GzipFile.__init__(self, filename, mode, compresslevel, fileobj)
        self._size = kwargs.get("size", self.SIZE)
        self._nltk_buffer = BytesIO()
        # cStringIO does not support len.
        self._len = 0

    def _reset_buffer(self):
        # For some reason calling BytesIO.truncate() here will lead to
        # inconsistent writes so just set _buffer to a new BytesIO object.
        self._nltk_buffer = BytesIO()
        self._len = 0

    def _write_buffer(self, data):
        # Simply write to the buffer and increment the buffer size.
        if data is not None:
            self._nltk_buffer.write(data)
            self._len += len(data)

    def _write_gzip(self, data):
        # Write the current buffer to the GzipFile.
        GzipFile.write(self, self._nltk_buffer.getvalue())
        # Then reset the buffer and write the new data to the buffer.
        self._reset_buffer()
        self._write_buffer(data)

    def close(self):
        # GzipFile.close() doesn't actuallly close anything.
        if self.mode == GZ_WRITE:
            self._write_gzip(None)
            self._reset_buffer()
        return GzipFile.close(self)

    def flush(self, lib_mode=FLUSH):
        self._nltk_buffer.flush()
        GzipFile.flush(self, lib_mode)

    def read(self, size=None):
        if not size:
            size = self._size
            contents = BytesIO()
            while True:
                blocks = GzipFile.read(self, size)
                if not blocks:
                    contents.flush()
                    break
                contents.write(blocks)
            return contents.getvalue()
        else:
            return GzipFile.read(self, size)

    def write(self, data, size=-1):
        """
        :param data: 要写入到文件或缓存的字节内容。
        :type data: bytes
        :param size: 写入文件之间的最小缓存值。
        :type size: int
        """
        if not size:
            size = self._size
        if self._len + len(data) <= size:
            self._write_buffer(data)
        else:
            self._write_gzip(data)


class GzipFileSystemPathPointer(FileSystemPathPointer):
    """
    一个 ``FileSystemPathPointer`` 文件系统路径指针的子类，
    用来识别一个压缩文件是否在给出的绝对路径上。
    对于加载大型压缩过的腌制对象来说， ``GzipFileSystemPathPointer`` 类是有效率的。
    """

    def open(self, encoding=None):
        # Note: In >= Python3.5, GzipFile is already using a
        # buffered reader in the backend which has a variable self._buffer
        # See https://github.com/nltk/nltk/issues/1308
        if sys.version.startswith("2.7") or sys.version.startswith("3.4"):
            stream = BufferedGzipFile(self._path, "rb")
        else:
            stream = GzipFile(self._path, "rb")
        if encoding:
            stream = SeekableUnicodeStreamReader(stream, encoding)
        return stream


class ZipFilePathPointer(PathPointer):
    """
    一个压缩文件路径指针，用来识别与压缩文件里的一个文件，
    通过读取压缩文件来访问其中的文件。
    """

    @py3_data
    def __init__(self, zipfile, entry=""):
        """
        建立一个新的路径指针，指向给出的压缩文件中描述的入口点。
        ``entry`` 参数使用相对路径，可以不带 `/` 斜杠绝对路径分隔符。

        :raise IOError: 如果压缩文件不存在，或压缩文件中没有所描述的入口点。
        """
        if isinstance(zipfile, string_types):
            zipfile = OpenOnDemandZipFile(os.path.abspath(zipfile))

        # Check that the entry exists:
        if entry:

            # Normalize the entry string, it should be relative:
            entry = normalize_resource_name(entry, True, "/").lstrip("/")

            try:
                zipfile.getinfo(entry)
            except Exception:
                # Sometimes directories aren't explicitly listed in
                # the zip file.  So if `entry` is a directory name,
                # then check if the zipfile contains any files that
                # are under the given directory.
                if entry.endswith("/") and [
                    n for n in zipfile.namelist() if n.startswith(entry)
                ]:
                    pass  # zipfile contains a file in that directory.
                else:
                    # Otherwise, complain.
                    raise IOError(
                        "Zipfile %r does not contain %r" % (zipfile.filename, entry)
                    )
        self._zipfile = zipfile
        self._entry = entry

    @property
    def zipfile(self):
        """一个实例只读属性。
        类型是 zipfile.ZipFile 对象，
        值是本路径指针实例识别的压缩文件含有的入口点。
        """
        return self._zipfile

    @property
    def entry(self):
        """一个实例只读属性。
        值是本路径指针示例所指向的压缩文件中的文件名。
        """
        return self._entry

    def open(self, encoding=None):
        data = self._zipfile.read(self._entry)
        stream = BytesIO(data)
        if self._entry.endswith(".gz"):
            # Note: In >= Python3.5, GzipFile is already using a
            # buffered reader in the backend which has a variable self._buffer
            # See https://github.com/nltk/nltk/issues/1308
            if sys.version.startswith("2.7") or sys.version.startswith("3.4"):
                stream = BufferedGzipFile(self._entry, fileobj=stream)
            else:
                stream = GzipFile(self._entry, fileobj=stream)
        elif encoding is not None:
            stream = SeekableUnicodeStreamReader(stream, encoding)
        return stream

    def file_size(self):
        return self._zipfile.getinfo(self._entry).file_size

    def join(self, fileid):
        entry = "%s/%s" % (self._entry, fileid)
        return ZipFilePathPointer(self._zipfile, entry)

    def __repr__(self):
        return str("ZipFilePathPointer(%r, %r)") % (self._zipfile.filename, self._entry)

    def __str__(self):
        return os.path.normpath(os.path.join(self._zipfile.filename, self._entry))


######################################################################
# Access Functions
######################################################################

# Don't use a weak dictionary, because in the common case this
# causes a lot more reloading that necessary.
_resource_cache = {}
"""A dictionary used to cache resources so that they won't
   need to be loaded more than once."""


def find(resource_name, paths=None):
    """一个访问函数。
    找到给出的资源，通过搜索路径中的目录和压缩文件，
    其中 ``paths`` 参数值是 ``None`` 或空字符串描述一个绝对路径时，
    返回一个相关的路径名。如果给出的资源没有找到，抛出一个 ``LookupError`` 例外错误，
    错误消息会给出一个 NLTK downloader 下载器帮助信息。

    压缩文件的处理机制：

      - 如果 ``resource_name`` 参数值中含有一个 ``.zip`` 扩展名的话，
        会认为是一个压缩文件；而 `paths` 参数值是查看压缩文件内部的路径。

      - 如果任何一种 ``nltk.data.path`` 形式中有一个 ``.zip`` 扩展名的话，
        会认为是一个压缩文件。

      - 如果给出的资源名不含任何压缩文件组成部分的话，
        那么 ``find()`` 函数会尝试第二套方案来找到资源，
        通过把路径中的 *p* 部分替换成 *p.zip/p* 来找资源。
        例如，第二套方案会让 ``find()`` 函数把资源名
        ``corpora/chat80/cities.pl`` 映射成一个压缩文件路径指针
        ``corpora/chat80.zip/chat80/cities.pl`` 形式。

      - 当使用 ``find()`` 函数来寻找压缩文件中的一个目录时，
        资源名必须用 ``/`` 斜杠来结尾。否则无法找到目录。

    :type resource_name: str 或 unicode
    :param resource_name: 要寻找的资源名。
        资源名都要是 posix-style 相对路径名，例如``corpora/brown`` 这种形式。
        目录名会自动转化成适合操作系统的路径分隔符。
    :rtype: str
    """
    resource_name = normalize_resource_name(resource_name, True)

    # Resolve default paths at runtime in-case the user overrides
    # nltk.data.path
    if paths is None:
        paths = path

    # Check if the resource name includes a zipfile name
    m = re.match(r"(.*\.zip)/?(.*)$|", resource_name)
    zipfile, zipentry = m.groups()

    # Check each item in our path
    for path_ in paths:
        # Is the path item a zipfile?
        if path_ and (os.path.isfile(path_) and path_.endswith(".zip")):
            try:
                return ZipFilePathPointer(path_, resource_name)
            except IOError:
                # resource not in zipfile
                continue

        # Is the path item a directory or is resource_name an absolute path?
        elif not path_ or os.path.isdir(path_):
            if zipfile is None:
                p = os.path.join(path_, url2pathname(resource_name))
                if os.path.exists(p):
                    if p.endswith(".gz"):
                        return GzipFileSystemPathPointer(p)
                    else:
                        return FileSystemPathPointer(p)
            else:
                p = os.path.join(path_, url2pathname(zipfile))
                if os.path.exists(p):
                    try:
                        return ZipFilePathPointer(p, zipentry)
                    except IOError:
                        # resource not in zipfile
                        continue

    # Fallback: if the path doesn't include a zip file, then try
    # again, assuming that one of the path components is inside a
    # zipfile of the same name.
    if zipfile is None:
        pieces = resource_name.split("/")
        for i in range(len(pieces)):
            modified_name = "/".join(pieces[:i] + [pieces[i] + ".zip"] + pieces[i:])
            try:
                return find(modified_name, paths)
            except LookupError:
                pass

    # Identify the package (i.e. the .zip file) to download.
    resource_zipname = resource_name.split("/")[1]
    if resource_zipname.endswith(".zip"):
        resource_zipname = resource_zipname.rpartition(".")[0]
    # Display a friendly error message if the resource wasn't found:
    msg = str(
        "Resource \33[93m{resource}\033[0m not found.\n"
        "Please use the NLTK Downloader to obtain the resource:\n\n"
        "\33[31m"  # To display red text in terminal.
        ">>> import nltk\n"
        ">>> nltk.download('{resource}')\n"
        "\033[0m"
    ).format(resource=resource_zipname)
    msg = textwrap_indent(msg)

    msg += "\n  For more information see: https://www.nltk.org/data.html\n"

    msg += "\n  Attempted to load \33[93m{resource_name}\033[0m\n".format(
        resource_name=resource_name
    )

    msg += "\n  Searched in:" + "".join("\n    - %r" % d for d in paths)
    sep = "*" * 70
    resource_not_found = "\n%s\n%s\n%s\n" % (sep, msg, sep)
    raise LookupError(resource_not_found)


def retrieve(resource_url, filename=None, verbose=True):
    """一个访问函数。
    把给出的资源复制到一个本地文件中。
    如果不描述 ``filename`` 参数值的话，会使用 URL 的文件名。
    如果如果已经有一个文件名叫 ``filename`` 的话，会抛出一个 ``ValueError`` 例外错误。

    :type resource_url: str
    :param resource_url: 描述资源的所在位置，也就是加载资源的地址。
        默认协议是 "nltk:" 也就是默认在 ``nltk_data`` 目录下寻找资源文件。
    """
    resource_url = normalize_resource_url(resource_url)
    if filename is None:
        if resource_url.startswith("file:"):
            filename = os.path.split(resource_url)[-1]
        else:
            filename = re.sub(r"(^\w+:)?.*/", "", resource_url)
    if os.path.exists(filename):
        filename = os.path.abspath(filename)
        raise ValueError("File %r already exists!" % filename)

    if verbose:
        print("Retrieving %r, saving to %r" % (resource_url, filename))

    # Open the input & output streams.
    infile = _open(resource_url)

    # Copy infile -> outfile, using 64k blocks.
    with open(filename, "wb") as outfile:
        while True:
            s = infile.read(1024 * 64)  # 64k blocks.
            outfile.write(s)
            if not s:
                break

    infile.close()


#: A dictionary describing the formats that are supported by NLTK's
#: load() method.  Keys are format names, and values are format
#: descriptions.
FORMATS = {
    "pickle": "一种序列化过的Python对象，使用pickle模块存储的对象。",
    "json": "一种序列化过的Python对象，使用json模块存储的对象。",
    "yaml": "一种序列化过的Python对象，使用yaml模块存储的对象。",
    "cfg": "一种语境自由语法。",
    "pcfg": "一种概率CFG对象。",
    "fcfg": "一种特性CFG对象。",
    "fol": "一种第一秩序逻辑表达式列表，使用"
    "nltk.sem.logic.Expression.fromstring进行语法分析。",
    "logic": "一种第一秩序逻辑表达式列表，使用"
    "nltk.sem.logic.LogicParser进行语法分析。需要一个额外的logic_parser参数。",
    "val": "一种语义验证，使用nltk.sem.Valuation.fromstring进行语法分析。",
    "raw": "一种使用生食（字节字符串）内容的文件。",
    "text": "一种使用生食（unicode字符串）内容的文件。",
}

#: A dictionary mapping from file extensions to format names, used
#: by load() when format="auto" to decide the format for a
#: given resource url.
AUTO_FORMATS = {
    "pickle": "pickle",
    "json": "json",
    "yaml": "yaml",
    "cfg": "cfg",
    "pcfg": "pcfg",
    "fcfg": "fcfg",
    "fol": "fol",
    "logic": "logic",
    "val": "val",
    "txt": "text",
    "text": "text",
}


def load(
    resource_url,
    format="auto",
    cache=True,
    verbose=False,
    logic_parser=None,
    fstruct_reader=None,
    encoding=None,
):
    """一个访问函数。
    从 ``nltk_data`` 目录中加载给出的资源。
    目前支持如下资源格式：

      - ``pickle``
      - ``json``
      - ``yaml``
      - ``cfg`` (语境自由语法格式)
      - ``pcfg`` (概率式CFG格式)
      - ``fcfg`` (基于特性的CFG格式)
      - ``fol`` (第一秩序逻辑公式格式)
      - ``logic`` (逻辑公式格式，语法分析器由``logic_parser``参数值提供。)
      - ``val`` (第一秩序逻辑模型的验证格式)
      - ``text`` (使用unicode编码的字符串作为内容的格式)
      - ``raw`` (使用字节字符串作为内容的文件格式)

    如果不描述 ``format`` 参数值的话，
     ``load()`` 函数会根据资源的文件扩展名来确定是哪种格式。
    如果加载失败， ``load()`` 函数会抛出一个 ``ValueError`` 例外错误。

    对于所有 ``text`` 格式来说（不是 ``pickle``, ``json``, ``yaml`` 和 ``raw`` 格式），
    函数会尝试使用UTF-8进行内容解码，如果还没有用的话，
    函数会尝试使用ISO-8859-1（拉丁语编码）进行内容解码，
    除非你用 ``encoding`` 参数明确地描述一种解码时使用的编码代号。

    :type resource_url: str
    :param resource_url: 要加载资源的地址。默认协议是 "nltk:" ，就是从
        ``nltk_data/``目录加载文件，即NLTK数据下载器下载的文件所在目录。
    :type cache: bool
    :param cache: 如果参数值是``True``的话，会把资源加载到缓存中，
        如果``find()``函数找到了缓存中的资源，
        函数会返回缓存里的资源，而不是重新加载资源。
    :type verbose: bool
    :param verbose: 如果参数值是``True``的话，当加载一项资源时会输出一个消息。
        当一项资源是从缓存中获得，就不回显示这个消息。
    :type logic_parser: LogicParser
    :param logic_parser: ``logic`` 资源格式会使用的语法分析器，用来分析逻辑表达式。
    :type fstruct_reader: FeatStructReader
    :param fstruct_reader: ``fcfg`` 资源格式会使用的语法分析器，用来分析特性结构。
    :type encoding: str
    :param encoding: 输入数据的编码代号；只能对 ``text`` 资源格式使用。
    """
    resource_url = normalize_resource_url(resource_url)
    resource_url = add_py3_data(resource_url)

    # Determine the format of the resource.
    if format == "auto":
        resource_url_parts = resource_url.split(".")
        ext = resource_url_parts[-1]
        if ext == "gz":
            ext = resource_url_parts[-2]
        format = AUTO_FORMATS.get(ext)
        if format is None:
            raise ValueError(
                "Could not determine format for %s based "
                'on its file\nextension; use the "format" '
                "argument to specify the format explicitly." % resource_url
            )

    if format not in FORMATS:
        raise ValueError("Unknown format type: %s!" % (format,))

    # If we've cached the resource, then just return it.
    if cache:
        resource_val = _resource_cache.get((resource_url, format))
        if resource_val is not None:
            if verbose:
                print("<<Using cached copy of %s>>" % (resource_url,))
            return resource_val

    # Let the user know what's going on.
    if verbose:
        print("<<Loading %s>>" % (resource_url,))

    # Load the resource.
    opened_resource = _open(resource_url)

    if format == "raw":
        resource_val = opened_resource.read()
    elif format == "pickle":
        resource_val = pickle.load(opened_resource)
    elif format == "json":
        import json
        from nltk.jsontags import json_tags

        resource_val = json.load(opened_resource)
        tag = None
        if len(resource_val) != 1:
            tag = next(resource_val.keys())
        if tag not in json_tags:
            raise ValueError("Unknown json tag.")
    elif format == "yaml":
        import yaml

        resource_val = yaml.load(opened_resource)
    else:
        # The resource is a text format.
        binary_data = opened_resource.read()
        if encoding is not None:
            string_data = binary_data.decode(encoding)
        else:
            try:
                string_data = binary_data.decode("utf-8")
            except UnicodeDecodeError:
                string_data = binary_data.decode("latin-1")
        if format == "text":
            resource_val = string_data
        elif format == "cfg":
            resource_val = nltk.grammar.CFG.fromstring(string_data, encoding=encoding)
        elif format == "pcfg":
            resource_val = nltk.grammar.PCFG.fromstring(string_data, encoding=encoding)
        elif format == "fcfg":
            resource_val = nltk.grammar.FeatureGrammar.fromstring(
                string_data,
                logic_parser=logic_parser,
                fstruct_reader=fstruct_reader,
                encoding=encoding,
            )
        elif format == "fol":
            resource_val = nltk.sem.read_logic(
                string_data,
                logic_parser=nltk.sem.logic.LogicParser(),
                encoding=encoding,
            )
        elif format == "logic":
            resource_val = nltk.sem.read_logic(
                string_data, logic_parser=logic_parser, encoding=encoding
            )
        elif format == "val":
            resource_val = nltk.sem.read_valuation(string_data, encoding=encoding)
        else:
            raise AssertionError(
                "Internal NLTK error: Format %s isn't "
                "handled by nltk.data.load()" % (format,)
            )

    opened_resource.close()

    # If requested, add it to the cache.
    if cache:
        try:
            _resource_cache[(resource_url, format)] = resource_val
            # TODO: add this line
            # print('<<Caching a copy of %s>>' % (resource_url,))
        except TypeError:
            # We can't create weak references to some object types, like
            # strings and tuples.  For now, just don't cache them.
            pass

    return resource_val


def show_cfg(resource_url, escape="##"):
    """一个访问函数。
    输出一个语法文件内容，忽略转义部分内容和空行内容。

    :type resource_url: str
    :param resource_url: 要加载的资源地址。默认协议是 "nltk:" 就是``nltk_data/``目录。
    :type escape: str
    :param escape: 语法文件内容中的注释部分会被忽略。
    """
    resource_url = normalize_resource_url(resource_url)
    resource_val = load(resource_url, format="text", cache=False)
    lines = resource_val.splitlines()
    for l in lines:
        if l.startswith(escape):
            continue
        if re.match("^$", l):
            continue
        print(l)


def clear_cache():
    """一个访问函数。
    删除资源缓存中的所有对象。
    :see: load()
    """
    _resource_cache.clear()


def _open(resource_url):
    """一个辅助函数。
    辅助函数根据给出的资源地址返回一个打开的文件对象。
    如果给出的资源地址使用了 "nltk:" 协议的话，
    或者不使用协议而使用 ``nltk.data.find`` 来指向一个路径，
    那就要给出打开文件的模式；
    如果资源地址使用了 'file' 协议的话，那么也要带着文件模式打开文件；
    否则，会委托成用 ``urllib2.urlopen`` 来打开资源地址。

    :type resource_url: str
    :param resource_url: 一个要加载的资源地址。默认协议是 "nltk:" ，
        就是``nltk_data/``目录所在位置。
    """
    resource_url = normalize_resource_url(resource_url)
    protocol, path_ = split_resource_url(resource_url)

    if protocol is None or protocol.lower() == "nltk":
        return find(path_, path + [""]).open()
    elif protocol.lower() == "file":
        # urllib might not use mode='rb', so handle this one ourselves:
        return find(path_, [""]).open()
    else:
        return urlopen(resource_url)


######################################################################
# Lazy Resource Loader
######################################################################

# We shouldn't apply @python_2_unicode_compatible
# decorator to LazyLoader, this is resource.__class__ responsibility.


class LazyLoader(object):
    @py3_data
    def __init__(self, _path):
        self._path = _path

    def __load(self):
        resource = load(self._path)
        # This is where the magic happens!  Transform ourselves into
        # the object by modifying our own __dict__ and __class__ to
        # match that of `resource`.
        self.__dict__ = resource.__dict__
        self.__class__ = resource.__class__

    def __getattr__(self, attr):
        self.__load()
        # This looks circular, but its not, since __load() changes our
        # __class__ to something new:
        return getattr(self, attr)

    def __repr__(self):
        self.__load()
        # This looks circular, but its not, since __load() changes our
        # __class__ to something new:
        return repr(self)


######################################################################
# Open-On-Demand ZipFile
######################################################################


class OpenOnDemandZipFile(zipfile.ZipFile):
    """
    这是 ``zipfile.ZipFile`` 的一个子类，不管什么时候都会关闭文件的指针；
    当需要从压缩文件读取数据时会重新打开指针。
    当一次性访问许多压缩文件时，对减少打开文件时的处理有用。
    对于 ``OpenOnDemandZipFile`` 类来说，必须用一个文件名来建立实例，
    而不能使用类似文件的对象（会导致重复打开对象的操作）。
    因为  ``OpenOnDemandZipFile`` 类是一种只读模式。
    （例如， ``write()`` 和 ``writestr()`` 方法都是被禁用的。）
    """

    @py3_data
    def __init__(self, filename):
        if not isinstance(filename, string_types):
            raise TypeError("ReopenableZipFile filename must be a string")
        zipfile.ZipFile.__init__(self, filename)
        assert self.filename == filename
        self.close()
        # After closing a ZipFile object, the _fileRefCnt needs to be cleared
        # for Python2and3 compatible code.
        self._fileRefCnt = 0

    def read(self, name):
        assert self.fp is None
        self.fp = open(self.filename, "rb")
        value = zipfile.ZipFile.read(self, name)
        # Ensure that _fileRefCnt needs to be set for Python2and3 compatible code.
        # Since we only opened one file here, we add 1.
        self._fileRefCnt += 1
        self.close()
        return value

    def write(self, *args, **kwargs):
        """:raise NotImplementedError: OpenOnDemandZipfile is read-only"""
        raise NotImplementedError("OpenOnDemandZipfile is read-only")

    def writestr(self, *args, **kwargs):
        """:raise NotImplementedError: OpenOnDemandZipfile is read-only"""
        raise NotImplementedError("OpenOnDemandZipfile is read-only")

    def __repr__(self):
        return repr(str("OpenOnDemandZipFile(%r)") % self.filename)


######################################################################
# { Seekable Unicode Stream Reader
######################################################################


class SeekableUnicodeStreamReader(object):
    """一个实例化类。
    一个流数据读取器类，它自动把源字节资源编码成unicode（像 ``codecs.StreamReader`` 一样）；
    但依然正确地支持 ``seek()`` 和 ``tell()`` 操作。
    相反， ``codecs.StreamReader`` 类不提供 ``seek()`` 和 ``tell()`` 方法。

    本类通过 ``StreamBackedCorpusView`` 类带动后大量使用
     ``seek()`` 和 ``tell()`` 方法，并且需要能够处理unicode编码的文件。

    注意：本类需要无状态解码器：对于我的知识来说，
    不应该导致任何Python内部unicode编码问题。
    """

    DEBUG = True  # : If true, then perform extra sanity checks.

    @py3_data
    def __init__(self, stream, encoding, errors="strict"):
        # Rewind the stream to its beginning.
        stream.seek(0)

        self.stream = stream
        """The underlying stream."""

        self.encoding = encoding
        """The name of the encoding that should be used to encode the
           underlying stream."""

        self.errors = errors
        """The error mode that should be used when decoding data from
           the underlying stream.  Can be 'strict', 'ignore', or
           'replace'."""

        self.decode = codecs.getdecoder(encoding)
        """The function that is used to decode byte strings into
           unicode strings."""

        self.bytebuffer = b""
        """A buffer to use bytes that have been read but have not yet
           been decoded.  This is only used when the final bytes from
           a read do not form a complete encoding for a character."""

        self.linebuffer = None
        """A buffer used by ``readline()`` to hold characters that have
           been read, but have not yet been returned by ``read()`` or
           ``readline()``.  This buffer consists of a list of unicode
           strings, where each string corresponds to a single line.
           The final element of the list may or may not be a complete
           line.  Note that the existence of a linebuffer makes the
           ``tell()`` operation more complex, because it must backtrack
           to the beginning of the buffer to determine the correct
           file position in the underlying byte stream."""

        self._rewind_checkpoint = 0
        """The file position at which the most recent read on the
           underlying stream began.  This is used, together with
           ``_rewind_numchars``, to backtrack to the beginning of
           ``linebuffer`` (which is required by ``tell()``)."""

        self._rewind_numchars = None
        """The number of characters that have been returned since the
           read that started at ``_rewind_checkpoint``.  This is used,
           together with ``_rewind_checkpoint``, to backtrack to the
           beginning of ``linebuffer`` (which is required by ``tell()``)."""

        self._bom = self._check_bom()
        """The length of the byte order marker at the beginning of
           the stream (or None for no byte order marker)."""

    # /////////////////////////////////////////////////////////////////
    # Read methods
    # /////////////////////////////////////////////////////////////////

    def read(self, size=None):
        """一个读取方法。
        根据字节量来读取内容，使用读取器的编码来进行解码，
        然后返回unicode字符串内容。

        :param size: 要读取的最大字节数量。如果没描述的话，会尽可能的读取大量字节内容。
        :type size: int
        :rtype: unicode
        """
        chars = self._read(size)

        # If linebuffer is not empty, then include it in the result
        if self.linebuffer:
            chars = "".join(self.linebuffer) + chars
            self.linebuffer = None
            self._rewind_numchars = None

        return chars

    def discard_line(self):
        if self.linebuffer and len(self.linebuffer) > 1:
            line = self.linebuffer.pop(0)
            self._rewind_numchars += len(line)
        else:
            self.stream.readline()

    def readline(self, size=None):
        """
        读取一行字节文本内容，使用读取器的编码进行解码，
        然后返回unicode字符串内容。

        :param size: 要读取的最大字节数量。如果在``size``读取完之前
            没有遇到新行符，那么返回值也许不是完整的单行字节文本内容。
        :type size: int

        :Example:
        
        >>> from io import StringIO, BytesIO
        >>> from nltk.data import SeekableUnicodeStreamReader

        >>> data_test = '实验流数据的不完整单行字节读取问题。'
        >>> stream1 = BytesIO(data_test.encode('utf8').decode('utf8').encode('utf8'))
        >>> stream2 = BytesIO(data_test.encode('utf8'))
        >>> reader1 = SeekableUnicodeStreamReader(stream1, 'utf8')
        >>> reader2 = SeekableUnicodeStreamReader(stream2, 'utf8')
        >>> print(reader1.readline(size=1))
        >>> print(reader2.readline(size=6))
        实
        实验

        """
        # If we have a non-empty linebuffer, then return the first
        # line from it.  (Note that the last element of linebuffer may
        # not be a complete line; so let _read() deal with it.)
        if self.linebuffer and len(self.linebuffer) > 1:
            line = self.linebuffer.pop(0)
            self._rewind_numchars += len(line)
            return line

        readsize = size or 72
        chars = ""

        # If there's a remaining incomplete line in the buffer, add it.
        if self.linebuffer:
            chars += self.linebuffer.pop()
            self.linebuffer = None

        while True:
            startpos = self.stream.tell() - len(self.bytebuffer)
            new_chars = self._read(readsize)

            # If we're at a '\r', then read one extra character, since
            # it might be a '\n', to get the proper line ending.
            if new_chars and new_chars.endswith("\r"):
                new_chars += self._read(1)

            chars += new_chars
            lines = chars.splitlines(True)
            if len(lines) > 1:
                line = lines[0]
                self.linebuffer = lines[1:]
                self._rewind_numchars = len(new_chars) - (len(chars) - len(line))
                self._rewind_checkpoint = startpos
                break
            elif len(lines) == 1:
                line0withend = lines[0]
                line0withoutend = lines[0].splitlines(False)[0]
                if line0withend != line0withoutend:  # complete line
                    line = line0withend
                    break

            if not new_chars or size is not None:
                line = chars
                break

            # Read successively larger blocks of text.
            if readsize < 8000:
                readsize *= 2

        return line

    def readlines(self, sizehint=None, keepends=True):
        """
        读取流数据内容，使用读取器的编码进行解码，
        返回由unicode内容行组成的一个列表。

        :rtype: 支持 ``list(unicode)`` 操作。
        :param sizehint: 以忽略，没有任何效果。
        :param keepends: 如果值为``False``的话，返回没有新行符的内容。
        """
        return self.read().splitlines(keepends)

    def next(self):
        """返回上游数据流中的下一行解码的内容。"""
        line = self.readline()
        if line:
            return line
        else:
            raise StopIteration

    def __next__(self):
        return self.next()

    def __iter__(self):
        """返回``self``"""
        return self

    def __del__(self):
        # let garbage collector deal with still opened streams
        if not self.closed:
            self.close()

    def xreadlines(self):
        """返回``self``"""
        return self

    # /////////////////////////////////////////////////////////////////
    # Pass-through methods & properties
    # /////////////////////////////////////////////////////////////////

    @property
    def closed(self):
        """判断是否已经关闭上游流数据的属性。"""
        return self.stream.closed

    @property
    def name(self):
        """判断上游流数据名字的属性，如果没有名字会抛出``AttributeError``例外错误。"""
        return self.stream.name

    @property
    def mode(self):
        """判断上游流数据打开模式的属性，如果没有模式会抛出``AttributeError``例外错误。"""
        return self.stream.mode

    def close(self):
        """
        关闭上游流数据的方法。
        """
        self.stream.close()

    # /////////////////////////////////////////////////////////////////
    # Seek and tell
    # /////////////////////////////////////////////////////////////////

    def seek(self, offset, whence=0):
        """一个移动读取指针起始位置的方法。
        把数据流移读取指针移动到新的位置上。
        如果读取器正在维护任何一种缓存时，那么缓存会被清除。

        :param offset: 字节内容的索引位偏移值。
        :param whence: 如果值是``0``的话，偏移值的起始位置就是流数据的开始位置
            （偏移值应该采用正整数）；如果值是``1``的话，偏移值的起始位置是流数据
            的当前位置（偏移值可以是正负整数）；又如果值是``2``的话，偏移值的起始
            位置是流数据的结束位置（偏移值应该典型是负整数）。
        """
        if whence == 1:
            raise ValueError(
                "Relative seek is not supported for "
                "SeekableUnicodeStreamReader -- consider "
                "using char_seek_forward() instead."
            )
        self.stream.seek(offset, whence)
        self.linebuffer = None
        self.bytebuffer = b""
        self._rewind_numchars = None
        self._rewind_checkpoint = self.stream.tell()

    def char_seek_forward(self, offset):
        """
        移动读取器指针向前移动 ``offset`` 值决定的字符数量，起到步幅的作用。
        即跳过多少个偏移位后作为开始读取的位置。``offset``不能是负数。
        """
        if offset < 0:
            raise ValueError("Negative offsets are not supported")
        # Clear all buffers.
        self.seek(self.tell())
        # Perform the seek operation.
        self._char_seek_forward(offset)

    def _char_seek_forward(self, offset, est_bytes=None):
        """
        根据``offset``值向前移动到流数据新位置上，
        不考虑所有缓存的长度。

        :param est_bytes: 一种提醒功能，给出一个估计字节数作为值，
            来决定 ``offset`` 会向前移动多少字符。
            默认值是 ``offset`` 的值。对``ascii``字符有影响。
        """
        if est_bytes is None:
            est_bytes = offset
        bytes = b""

        while True:
            # Read in a block of bytes.
            newbytes = self.stream.read(est_bytes - len(bytes))
            bytes += newbytes

            # Decode the bytes to characters.
            chars, bytes_decoded = self._incr_decode(bytes)

            # If we got the right number of characters, then seek
            # backwards over any truncated characters, and return.
            if len(chars) == offset:
                self.stream.seek(-len(bytes) + bytes_decoded, 1)
                return

            # If we went too far, then we can back-up until we get it
            # right, using the bytes we've already read.
            if len(chars) > offset:
                while len(chars) > offset:
                    # Assume at least one byte/char.
                    est_bytes += offset - len(chars)
                    chars, bytes_decoded = self._incr_decode(bytes[:est_bytes])
                self.stream.seek(-len(bytes) + bytes_decoded, 1)
                return

            # Otherwise, we haven't read enough bytes yet; loop again.
            est_bytes += offset - len(chars)

    def tell(self):
        """
        在上游流数据返回当前字节位置。
        如果读取器正在维护任何一种缓存时，
        返回的位置会是缓存的开始位置。
        """
        # If nothing's buffered, then just return our current filepos:
        if self.linebuffer is None:
            return self.stream.tell() - len(self.bytebuffer)

        # Otherwise, we'll need to backtrack the filepos until we
        # reach the beginning of the buffer.

        # Store our original file position, so we can return here.
        orig_filepos = self.stream.tell()

        # Calculate an estimate of where we think the newline is.
        bytes_read = (orig_filepos - len(self.bytebuffer)) - self._rewind_checkpoint
        buf_size = sum(len(line) for line in self.linebuffer)
        est_bytes = int(
            (bytes_read * self._rewind_numchars / (self._rewind_numchars + buf_size))
        )

        self.stream.seek(self._rewind_checkpoint)
        self._char_seek_forward(self._rewind_numchars, est_bytes)
        filepos = self.stream.tell()

        # Sanity check
        if self.DEBUG:
            self.stream.seek(filepos)
            check1 = self._incr_decode(self.stream.read(50))[0]
            check2 = "".join(self.linebuffer)
            assert check1.startswith(check2) or check2.startswith(check1)

        # Return to our original filepos (so we don't have to throw
        # out our buffer.)
        self.stream.seek(orig_filepos)

        # Return the calculated filepos
        return filepos

    # /////////////////////////////////////////////////////////////////
    # Helper methods
    # /////////////////////////////////////////////////////////////////

    def _read(self, size=None):
        """这是一个辅助方法。
        从上游流数据读取 ``size`` 值数量的字节，
        使用读取器的编码对字节进行解码，然后返回unicode字符串。
        在结果中不含有 ``linebuffer`` 值。
        """
        if size == 0:
            return ""

        # Skip past the byte order marker, if present.
        if self._bom and self.stream.tell() == 0:
            self.stream.read(self._bom)

        # Read the requested number of bytes.
        if size is None:
            new_bytes = self.stream.read()
        else:
            new_bytes = self.stream.read(size)
        bytes = self.bytebuffer + new_bytes

        # Decode the bytes into unicode characters
        chars, bytes_decoded = self._incr_decode(bytes)

        # If we got bytes but couldn't decode any, then read further.
        if (size is not None) and (not chars) and (len(new_bytes) > 0):
            while not chars:
                new_bytes = self.stream.read(1)
                if not new_bytes:
                    break  # end of file.
                bytes += new_bytes
                chars, bytes_decoded = self._incr_decode(bytes)

        # Record any bytes we didn't consume.
        self.bytebuffer = bytes[bytes_decoded:]

        # Return the result
        return chars

    def _incr_decode(self, bytes):
        """一个辅助方法。
        把提供的字节解码成unicode字符串，
        使用读取器的编码进行解码。如果由于
        一个字节切分错误导致例外错误发生，那么
        解码的字节字符串中不含有产生字节切分错误的字节。

        返回一个元组 ``(chars, num_consumed)`` 形式，
        其中 ``chars`` 是解码完的unicode字符串，
        而 ``num_consumed`` 是吃掉的字节数量。
        """
        while True:
            try:
                return self.decode(bytes, "strict")
            except UnicodeDecodeError as exc:
                # If the exception occurs at the end of the string,
                # then assume that it's a truncation error.
                if exc.end == len(bytes):
                    return self.decode(bytes[: exc.start], self.errors)

                # Otherwise, if we're being strict, then raise it.
                elif self.errors == "strict":
                    raise

                # If we're not strict, then re-process it with our
                # errors setting.  This *may* raise an exception.
                else:
                    return self.decode(bytes, self.errors)

    _BOM_TABLE = {
        "utf8": [(codecs.BOM_UTF8, None)],
        "utf16": [(codecs.BOM_UTF16_LE, "utf16-le"), (codecs.BOM_UTF16_BE, "utf16-be")],
        "utf16le": [(codecs.BOM_UTF16_LE, None)],
        "utf16be": [(codecs.BOM_UTF16_BE, None)],
        "utf32": [(codecs.BOM_UTF32_LE, "utf32-le"), (codecs.BOM_UTF32_BE, "utf32-be")],
        "utf32le": [(codecs.BOM_UTF32_LE, None)],
        "utf32be": [(codecs.BOM_UTF32_BE, None)],
    }

    def _check_bom(self):
        # Normalize our encoding name
        enc = re.sub("[ -]", "", self.encoding.lower())

        # Look up our encoding in the BOM table.
        bom_info = self._BOM_TABLE.get(enc)

        if bom_info:
            # Read a prefix, to check against the BOM(s)
            bytes = self.stream.read(16)
            self.stream.seek(0)

            # Check for each possible BOM.
            for (bom, new_encoding) in bom_info:
                if bytes.startswith(bom):
                    if new_encoding:
                        self.encoding = new_encoding
                    return len(bom)

        return None


__all__ = [
    "path",
    "PathPointer",
    "FileSystemPathPointer",
    "BufferedGzipFile",
    "GzipFileSystemPathPointer",
    "GzipFileSystemPathPointer",
    "find",
    "retrieve",
    "FORMATS",
    "AUTO_FORMATS",
    "load",
    "show_cfg",
    "clear_cache",
    "LazyLoader",
    "OpenOnDemandZipFile",
    "GzipFileSystemPathPointer",
    "SeekableUnicodeStreamReader",
]
