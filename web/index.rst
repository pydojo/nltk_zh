自然语言工具集
========================

NLTK 是使用人类语言数据建立 Python 程序的领头羊。
工具集提供了简单实用的接口， `超过 50 个文集和词汇资源 <http://nltk.org/nltk_data/>`_ 例如词网，
还提供了文字处理库套装，针对分类、令牌、词干、标签、语法分析，以及语义根源处理，
甚至工业级 NLP 库的打包器和一个活跃的 `讨论组 <http://groups.google.com/group/nltk-users>`_ 。

感谢介绍编程基础的指导手册，还有在计算机语言学上的众多话题，另外感谢理解性的 API 文档内容。
NLTK 受众群广泛，适合语言学家、工程师、学生、教育工作者、研究员和工业用户们的青睐。
NLTK 可以用在三大操作系统上，分别是 Windows 系统、Mac OS X 系统、Linux 系统。最棒的就是 NLTK 是免费的、开源的、社区带动的项目。

NLTK 曾被美誉为 “使用 Python 把教学与工作结合在计算机语言学领域的美妙工具。” 以及
“与自然语言一起玩耍的梦幻库。”

`用 Python 自然语言处理 <http://nltk.org/book>`_ 一书提供了实际的编程语言处理介绍。
作者就是 NLTK 的建造者们，本书指导了读者，涉及内容有：书写 Python 程序的基础知识、
与文集一起工作、分类文字、分析语言结构，等等众多内容。
本书的在线版本已经更新成 Python 3 和 NLTK 3 系列。
(原来的 Python 2 版本依然可以在如下网站找到 `http://nltk.org/book_1ed <http://nltk.org/book_1ed>`_)

与 NLTK 一起做些简单的事情
---------------------------------------

令牌和标签一些文字：

    >>> import nltk
    >>> sentence = """At eight o'clock on Thursday morning
    ... Arthur didn't feel very good."""
    >>> tokens = nltk.word_tokenize(sentence)
    >>> tokens
    ['At', 'eight', "o'clock", 'on', 'Thursday', 'morning',
    'Arthur', 'did', "n't", 'feel', 'very', 'good', '.']
    >>> tagged = nltk.pos_tag(tokens)
    >>> tagged[0:6]
    [('At', 'IN'), ('eight', 'CD'), ("o'clock", 'JJ'), ('on', 'IN'),
    ('Thursday', 'NNP'), ('morning', 'NN')]

识别署名实体：

    >>> entities = nltk.chunk.ne_chunk(tagged)
    >>> entities
    Tree('S', [('At', 'IN'), ('eight', 'CD'), ("o'clock", 'JJ'),
               ('on', 'IN'), ('Thursday', 'NNP'), ('morning', 'NN'),
           Tree('PERSON', [('Arthur', 'NNP')]),
               ('did', 'VBD'), ("n't", 'RB'), ('feel', 'VB'),
               ('very', 'RB'), ('good', 'JJ'), ('.', '.')])

显示一颗语法树：

    >>> from nltk.corpus import treebank
    >>> t = treebank.parsed_sents('wsj_0001.mrg')[0]
    >>> t.draw()

.. image:: images/tree.gif

如果你要使用 NLTK 做出版工作，请引用如下 NLTK 图书的如下内容：

	Bird, Steven, Edward Loper and Ewan Klein (2009), *Natural Language Processing with Python*.  O'Reilly Media Inc.

接下来做什么？
---------------

* `注册发布通告群 <http://groups.google.com/group/nltk>`_
* `加入讨论 <http://groups.google.com/group/nltk-users>`_

文档内容
===========


.. toctree::
   :maxdepth: 1

   news
   install
   data
   contribute
   FAQ <https://github.com/nltk/nltk/wiki/FAQ>
   Wiki <https://github.com/nltk/nltk/wiki> 
   API <api/nltk>
   HOWTO <http://www.nltk.org/howto>

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
