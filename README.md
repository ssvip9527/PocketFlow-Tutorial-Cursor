<h1 align="center">用Cursor构建Cursor</h1>

Cursor很酷！但如果我们用它来构建一个开源的、可定制的AI编码代理呢？我们将开发一个"Cursor代理"，它可以编写、审查和重构代码——就在Cursor内部。这是元编程，它是可修改的，它由Cursor的力量驱动。让我们用Cursor来构建Cursor。

<p align="center">
  <a href="https://youtu.be/HH7TZFgoqEQ" target="_blank">
    <img 
      src="./assets/banner.png" width="600"
    />
  </a>
</p>

- 安装：
  ```bash
  pip install -r requirements.txt
  ```

- 运行代理
  ```bash
  python main.py --query "For Trusted by industry leaders, add two more boxes." --working-dir ./project
  ```

- **它是如何工作的？** 学习的最佳起点是[设计文档](docs/design.md)和[流程代码](flow.py)。

- **注意**：这个项目还没有经过压力测试或优化。我们故意保持简单以便学习。

## 我使用Cursor本身构建了这个Cursor代理！

- 我使用[**代理编码**](https://the-pocket.github.io/PocketFlow/guide.html)构建，这是最快的开发范式，人类只需[设计](docs/design.md)，代理负责[编码](flow.py)。

- 秘密武器是[Pocket Flow](https://github.com/The-Pocket/PocketFlow)，一个100行的LLM框架，让代理（如Cursor AI）为你构建
  
- 逐步YouTube开发教程：

  <br>
  <div align="center">
    <a href="https://youtu.be/HH7TZFgoqEQ" target="_blank">
      <img src="./assets/tutorial.png" width="500" alt="IMAGE ALT TEXT" style="cursor: pointer;">
    </a>
  </div>
  <br>

## 示例

我们提供了一个SaaS产品主页的示例`project`，供代码代理编辑。

运行页面：

```
cd project
npm install
npm run dev
```

以下是一些你可以尝试的示例查询：
```bash
python main.py --query "For Trusted by industry leaders, add two more boxes." --working-dir ./project
```
