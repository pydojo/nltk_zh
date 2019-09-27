# 对 NLTK 做出的贡献

大家好！感谢为 [NLTK](http://www.nltk.org/) 做贡献有兴趣。
:-) 你会加入到一个 [贡献者长名单](https://github.com/nltk/nltk/blob/develop/AUTHORS.md)。
在本篇文档中，我们会尽力总结你需要知道的每一件事，这样就能做好工作。


## 代码与问题

我们使用 [GitHub](https://www.github.com/) 来服务我们的代码仓库和问题。
其中 [ GitHub 上的 NLTK 组织](https://github.com/nltk) 有许多仓库，
所以我们可以更好地管理问题和开发。最重要的事情是:

- [nltk/nltk](https://github.com/nltk/nltk/) 与安装库相关的代码主仓库；
- [nltk/nltk_data](https://github.com/nltk/nltk_data) 仓库中含有与
  文集、标签相关的数据，以及其它没有默认包含在安装库中的有用数据，你可以通过
   `nltk.downloader` 来进行下载；
- [nltk/nltk.github.com](https://github.com/nltk/nltk.github.com) NLTK 网址
  所含的信息包括了安装库、文档、下载 NLTK 图书的链接，等等内容；
- [nltk/nltk_book](https://github.com/nltk/nltk_book) NLTK 图书的源代码。

## 开发优先级

NLTK 功能的组成是由 Python/NLP 社区推动贡献着的。
优先开发的领域都罗列在 [NLTK Wiki](https://github.com/nltk/nltk/wiki#development) 上。

## Git 与我们的分支模式

### Git

我们使用 [Git](http://git-scm.com/) 作为 [版本控制系统](http://en.wikipedia.org/wiki/Revision_control) ，所以贡献的
最好方式就是学习如何使用 Git 以及把你的变更放到一个 Git 仓库中。
这里有大量关于 Git 的文档 -- 你可以从这里开始 [专家级 Git 
工具书](http://git-scm.com/book/)


### 搭建一个开发环境

为主仓库做贡献要建立你的本地开发环境 [nltk/nltk](https://github.com/nltk/nltk/)：

- 用你的 GitHub 账户叉起 [nltk/nltk](https://github.com/nltk/nltk/) 仓库；
- 把你自己叉起的仓库复制到本地硬盘中
  (`git clone https://github.com/<your-github-username>/nltk.git`)；
- 运行 `cd nltk` 进入 `nltk` 代码基地的根目录；
- 安装依赖包 (`pip install -r pip-req.txt`)；
- 为运行测试下载数据集 (`python -m nltk.downloader all`)；
- 建立一个从你的本地仓库连接到上游的远程链接，指向 GitHub 上的 `nltk/nltk` 
  (`git remote add upstream https://github.com/nltk/nltk.git`) --
  你会需要使用这个 `upstream` 链接来把你的本地仓库左右最近的贡献更新到官方主仓库。

### GitHub 拉取请求

我们使用著名的
[gitflow](http://nvie.com/posts/a-successful-git-branching-model/) 来管理我们的分支。

总结一下我们的 git 分支模式:
- 进入 `develop` 开发分支 (`git checkout develop`)；
- 从上游 `nltk/nltk` 主仓库获得所有最近的工作
  (`git pull upstream develop`)；
- 建立一个新的 `develop` 开发分支，含有一个描述的名字 (例如：
  `feature/portuguese-sentiment-analysis` 、 `hotfix/bug-on-downloader`)。
  你可以切换到 `develop` 开发分支 (`git checkout develop`) ，然后建立一个新开发
  分支 (`git checkout -b name-of-the-new-branch`)；
- 在本地的新开发分支上做一些少量变更和提交 (`git add files-changed` 、
  `git commit -m "Add some change"`)；
- 运行测试来确保不会出现什么问题
  (`tox -e py35` 如果你使用的是 Python 3.5)；
- 把你的名字增加到 `AUTHORS.md` 文件中，这样就成为一名贡献者了；
- 把你的叉子版本推送到 GitHub 上 (使用你的本地分支名：
  `git push origin branch-name`)；
- 使用 GitHub 网站接口建立一个拉取请求 (告诉我们从你的新分支上拉取变更，
  然后会加入到我们的 `develop` 分支上)；
- 等待注释。


### 提示

- 写一些 [有帮助的提交
  消息](http://robots.thoughtbot.com/5-useful-tips-for-a-better-commit-message)
- 任何位于 `develop` 开发分支的内容都应该是具有可开发性的 (不要有测试失败情况)。
- 永远不要使用 `git add .` 命令：这会把不期望的文件也加入其中；
- 避免使用 `git commit -a` 命令，除非你知道你正在干什么；
- 检查每一个变更，使用 `git diff` 命令，没有问题再加入到索引中 (平台
  区域) 接着使用 `git diff --cached` 命令后再做提交；
- 确保把你的名字增加到我们的[贡献者名单](https://github.com/nltk/nltk/blob/develop/AUTHORS.md)中；
- 如果你推送主仓库的访问，请不要直接提交到
   `develop` 开发仓库：你的访问应该只用来接收拉取请求；如果你想要增加一个新特性的话，
  你应该使用与其他开发者们使用的相同步骤，这样你的代码才会被审阅。
- 阅读 [RELEASE-HOWTO.txt](RELEASE-HOWTO.txt) 内容来查看你需要知道的每一件事，
  否则就不要建立一个新的 NLTK 发布版本。


## 代码指导

- 使用 [PEP8](http://www.python.org/dev/peps/pep-0008/)；
- 为你增加的新特性写测试 (请阅读下面 "测试" 话题部分)；
- 一直要记住 [注释过的代码是
  死代码](http://www.codinghorror.com/blog/2008/07/coding-without-comments.html);
- 命名识别符 (变量名、类名、函数名、模块名) 使用适合人类阅读
  的名字 (`x` 就不适合人类阅读)；
- 当操作字符串时，使用 [Python 的新风格
  格式化](http://docs.python.org/library/string.html#format-string-syntax)
  (使用 `'{} = {}'.format(a, b)` 而不要使用 `'%s = %s' % (a, b)` 这种 Python 2 的风格);
- 所有 `#TODO` 注释都会转入到问题里去 (使用我们的
  [GitHub 问题系统](https://github.com/nltk/nltk/issues))；
- 运行所有测试后再执行推送 (只可以执行 `tox`) 因为如果你的代码变更导致断裂问题，你会知道的；
- 尽量写兼容 Python 2 的代码，最好是适合 Python3 的代码，因为对于我们来说
  支持这两个系列版本就不会那么痛苦了。

也要阅读我们的 [开发者指导](https://github.com/nltk/nltk/wiki/Developers-Guide)


## 测试

你应该写的测试是给每一个你增加的特性做测试，或者是为你所解决代码中 bug 的测试用例。
为我们的每一行代码执行自动化测试，会让我们没有顾虑去做出大量变更：
因为如果变更导致了一些 bug 的话，或者导致一些特性缺失，测试会一直能够做出验证。
如果我们不做测试工作，我们会像盲人摸象一样，并且每一个变更会伴随一些断裂现象出现
而带来一些担忧。

对于你的代码更好的一种设计来说，我们建议使用一项 TDD 技术，名叫
[测试带动开发](https://en.wikipedia.org/wiki/Test-driven_development)，
就是你先写测试用例，这样在写生产代码**之前**可以实现你所期望的特性。


## 持续集成

**已淘汰的：** NLTK 曾使用 [Cloudbees](https://nltk.ci.cloudbees.com/) 来做持续集成。

NLTK 现在使用 [Travis](https://travis-ci.org/nltk/nltk/) 做持续集成。

其中 [`.travis.yml`](https://github.com/nltk/nltk/blob/travis/.travis.yml) 文件
是配置服务器用的：

 - `matrix: include:` section 
   - tests against supported Python versions (2.7, 3.5 and 3.6) 
     - all python versions run the `py-travis` tox test environment in the [`tox.ini`](https://github.com/nltk/nltk/blob/travis/tox.ini#L105) file
   - tests against Python 3.6 for third-party tools APIs

 - `before_install:` section 
   - checks the Java and Python version calling the `tools/travis/pre-install.sh` script
   - changes the permission for `tools/travis/coverage-pylint.sh` to allow it to be executable
   - changes the permission for `tools/travis/third-party.sh` to allow it to be executable
   
 - `install` section
   - the `tools/travis/install.sh` installs the `pip-req.txt` for NLTK and the necessary python packages for CI testing
   - install `tox` for testing
    
 - `py-travis` tox test environment generally 
   - the `extras = all` dependencies in needed to emulate `pip install nltk[all]`, see https://tox.readthedocs.io/en/latest/config.html#confval-extras=MULTI-LINE-LIST
   - for the `py-travis-third-party` build, it will run `tools/travis/third-party.sh` to install third-party tools (Stanford NLP tools and CoreNLP and SENNA)
   - calls `tools/travis/coverage-pylint.sh` shell script that calls the `nltk/nltk/test/runtests.py` with [`coverage`](https://pypi.org/project/coverage/) and 
   - calls `pylint` # Currently, disabled because there's lots to clean...

   - before returning a `true` to state that the build is successful
    
    
#### 在本地使用 `tox` 做测试

第一步就是搭建一个新的虚拟环境，阅读 https://docs.python-guide.org/dev/virtualenvs/
然后运行 `tox -e py37` 命令。

例如，使用 `pipenv` 时：

```
git clone https://github.com/nltk/nltk.git
cd nltk
pipenv install -r pip-req.txt
pipenv install tox
tox -e py37
```
 

# 讨论

我们在 Google 群组上有 3 个邮箱列表:

- [nltk][nltk-announce]，只做通告使用；
- [nltk-users][nltk-users]，为通用讨论和用户问题使用；
- [nltk-dev][nltk-dev]，为 NLTK 开发感兴趣的人提供使用。

如果你有任何问题或建议，通过 [nltk-dev][nltk-dev] 开发邮件列表联系我们，
请别受拘束。每一份贡献都是非常受欢迎的！

挥舞你的屠龙刀吧！ :-p 未经 Python3.7 环境测试的部分不进行汉化。

[nltk-announce]: https://groups.google.com/forum/#!forum/nltk
[nltk-dev]: https://groups.google.com/forum/#!forum/nltk-dev
[nltk-users]: https://groups.google.com/forum/#!forum/nltk-users
