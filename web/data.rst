安装 NLTK 数据
====================

NLTK 伴随了许多文集、语法工具、训练完的模型，等等内容。一个完整的清单发布地址是： http://nltk.org/nltk_data/

要安装数据，首先安装 NLTK (阅读 http://nltk.org/install.html 文档内容)，然后使用 NLTK 的数据下载器，下面会介绍。

数据都是分成了一个个独立的数据包，你可以下载整个数据集 (使用 "all" 作为参数值)；或者只下载需要的数据包，例如为本书中示例和练习使用的数据包 (使用 "book" 作为参数值)；又或者只下载文集和无语法或训练完的模型所需的数据包 (使用 "all-corpora" 作为参数值)。

互动方式的安装
---------------------

*为中心安装提供给多个用户使用，用管理员账户来做下面的操作。*

进入 Python REPL 后输入：

    >>> import nltk
    >>> nltk.download()

一个新窗口会打开，显示 NLTK 下载器。点击文件菜单后选择改变下载目录。对于中心安装来说，下载目录要设置成 ``C:\nltk_data`` (Windows)， ``/usr/local/share/nltk_data`` (Mac)， ``/usr/share/nltk_data`` (Unix)。然后就是选择你要下载的内容。

如果你不把数据安装到上面三个位置之一的话，你还需要设置 ``NLTK_DATA`` 环境变量，描述变量所指的数据所在位置。 (在 Windows 系统上，鼠标右键点“我的电脑”后选择 ``Properties > Advanced > Environment Variables > User Variables > New...``)

测试是否已经安装完下载的数据。（例子中的代码是假设你下载完了布朗文集）：

    >>> from nltk.corpus import brown
    >>> brown.words()
    ['The', 'Fulton', 'County', 'Grand', 'Jury', 'said', ...]

通过代理服务器来安装
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

如果你的网络连接需要使用一个代理服务器的话，你应该把代理地址描述出来。在一个授权的代理环境中，要填写一个用户名和密码。如果代理设置成空内容的话，下面这个函数会检查系统代理。

    >>> nltk.set_proxy('http://proxy.example.com:3128', ('USERNAME', 'PASSWORD'))
    >>> nltk.download() 

命令行安装方法
-------------------------

下载器会搜索已有的一个 ``nltk_data`` 目录，把数据安装到这个目录里。如果这个目录不存在的话，会先建立这个目录到中心位置上 (当使用一个管理员账号时) 否则就是建立在当前用户的文件空间里。如果需要的话使用管理员账号来下载数据，或者使用 sudo 前置命令下载数据。不同系统的推荐数据目录位置是： ``C:\nltk_data`` (Windows)， ``/usr/local/share/nltk_data`` (Mac)，和 ``/usr/share/nltk_data`` (Unix)。你可以使用 ``-d`` 旗语来描述一个不同的位置（但是，如果使用了这个旗语的话，就要设置环境变量 ``NLTK_DATA`` 指向你自定义的下载位置）。

运行命令是 ``python -m nltk.downloader all``。要确保下载到中心位置，运行命令是 ``sudo python -m nltk.downloader -d /usr/local/share/nltk_data all``

Windows系统：使用开始菜单中的“运行”选项来输入命令也可以。

安装后的测试：检查用户环境和用户权限都正确地进行了设置，通过登陆一名用户账户来测试，进入 REPL 后使用布朗文集示例即可（前面已经提到过）。

手动安装
-------------------

新建一个 ``nltk_data`` 目录，例如： ``C:\nltk_data`` 或 ``/usr/local/share/nltk_data`` 文件夹，
然后建立其中的子目录： ``chunkers``、``grammars``、``misc``、``sentiment``、``taggers``、``corpora``、``help``、``models``、``stemmers``、``tokenizers``。

从 ``http://nltk.org/nltk_data/`` 下载单个数据包（查看 "download" 超链接）。
把数据包解压到相符的子目录里。例如，布朗文集数据包在：
``https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/corpora/brown.zip`` 地址上，解压到 ``nltk_data/corpora/brown`` 子目录中。

设置 ``NLTK_DATA`` 环境变量指向到数据所在的顶层目录 ``nltk_data`` 位置上。




