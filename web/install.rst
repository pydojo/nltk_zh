安装 NLTK
===============

NLTK 需要使用 Python 版本有 3.5、 3.6 或 3.7

对于 Windows 系统的用户们，强烈推荐本篇指导来安装 Python 3 https://docs.python-guide.org/starting/install3/win/#install3-windows 以便成功。

搭建一个 Python 虚拟环境 (Mac/Unix/Windows)
--------

请通过本篇指导来学习如何管理你的虚拟环境，这是要在你安装 NLTK 之前完成的事情， https://docs.python-guide.org/dev/virtualenvs/

另外，你可以使用 Anaconda 分发版安装器，其中伴随了许多 "已含有的能量库" https://www.anaconda.com/distribution/ 

Mac/Unix 系统
--------

#. 安装 NLTK 的命令是： ``pip install --user -U nltk``
#. 安装 Numpy (可选) 的命令是： ``pip install --user -U numpy``
#. 测试安装是否成功的命令是：终端里输入 ``python`` 进入 REPL 后输入 ``import nltk`` 无错误提示即可。

对于老旧的 Python 版本来说，也许要安装 setuptools 库 (阅读 http://pypi.python.org/pypi/setuptools) 和 pip 应用管理器 (``sudo easy_install pip``)。

Windows 系统
-------

如下指导是假设你还没有把 Python 安装到你的电脑时的情况。

32-bit 二进制安装
~~~~~~~~~~~~~~~~~~~~~~~~~~

#. 安装 Python 3.7 的 32位程序： http://www.python.org/downloads/ (不要安装 64-bit 版本)
#. 安装 Numpy (可选)： https://www.scipy.org/scipylib/download.html
#. 安装 NLTK： http://pypi.python.org/pypi/nltk
#. 安装完的测试： ``Start>Python37`` 进入 Python REPL 后输入 ``import nltk``

安装第三方软件
-------------------------------

请阅读： https://github.com/nltk/nltk/wiki/Installing-Third-Party-Software 文档内容。


安装 NLTK 数据
-------------------------------

安装完 NLTK 工具集后，请一定要安装需要的数据集和模型，这样具体的函数才可以有效。

如果你不知道你要使用哪个数据集和模型，你可以安装 NLTK 数据中“受欢迎”的子集，在命令行里输入 `python -m nltk.downloader popular` 命令，或者在 Python REPL 中输入 `import nltk; nltk.download('popular')` 代码。

对于数据的详细内容，阅读 http://www.nltk.org/data.html 文档内容。
