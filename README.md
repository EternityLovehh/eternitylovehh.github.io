# 王大人的博客 · 源码仓库

[![Deploy](https://github.com/EternityLovehh/eternitylovehh.github.io/actions/workflows/deploy.yml/badge.svg)](https://github.com/EternityLovehh/eternitylovehh.github.io/actions/workflows/deploy.yml)

线上地址:<https://eternitylovehh.github.io/>

- **框架**:Hexo 5.4 + Butterfly 3.6.2 主题
- **分支模型**:
  - `dev`(本分支)→ Hexo 源码(Markdown 文章、配置、主题)
  - `master` → GitHub Actions 自动构建出的 HTML(请勿手动改)
- **部署方式**:推送 `dev` 后,GitHub Actions 自动构建并推到 `master`,GitHub Pages 自动上线。**任何设备的浏览器都能写博客,不需要本地安装 Node/Hexo。**

---

## 📝 写一篇新文章(浏览器即可,推荐)

1. 打开仓库:<https://github.com/EternityLovehh/eternitylovehh.github.io>
2. 切到 **`dev`** 分支
3. **按英文句号键 `.`**(或把 URL 里 `github.com` 改成 `github.dev`),进入网页版 VS Code
4. 在 `source/_posts/` 目录下新建文件,例如 `my-post.md`
5. 粘贴模板并填写内容:

   ```markdown
   ---
   title: 文章标题
   date: 2026-05-12 16:00:00
   tags: [Android, java]
   categories: [技术]
   ---

   正文从这里开始……
   ```

6. 左侧栏 **Source Control**(Ctrl/Cmd + Shift + G)→ 输入 commit message → 点 **Commit & Push**
7. ☕ 1-2 分钟后访问 <https://eternitylovehh.github.io/> 即可看到新文章
   - 构建进度:<https://github.com/EternityLovehh/eternitylovehh.github.io/actions>

> 文件名用英文/拼音,URL 会按 `_config.yml` 的 `permalink: :year/:month/:day/:title/` 生成。

---

## 🎨 改样式 / 改主题

| 想做的事 | 改哪个文件 |
|---|---|
| 改站点标题 / 作者 / URL / 菜单 | `_config.yml` |
| 改主题外观(颜色、布局、社交链接、评论、首页背景) | `_config.butterfly.yml` |
| 写自定义 CSS(微调) | `source/css/custom.css`(若不存在自行新建,并在 `_config.butterfly.yml` 的 `inject.head` 引入) |
| 改主题模板 HTML 结构 | `themes/Butterfly/layout/*.pug` |
| 改主题原生样式 | `themes/Butterfly/source/css/**/*.styl` |
| 加/删 Hexo 插件 | `package.json` 的 `dependencies` |

改完保存 → commit → push,流程同写文章。

---

## 🖥️ 本地预览(可选)

只有在想本地实时预览样式时才需要。

```bash
# 第一次:
git clone https://github.com/EternityLovehh/eternitylovehh.github.io.git
cd eternitylovehh.github.io
git checkout dev
nvm use 20            # Node 20(本仓库用这个版本构建)
npm install --registry=https://registry.npmmirror.com

# 启动本地服务器,访问 http://localhost:4000
npx hexo clean && npx hexo server
```

注意:**不要**手动 `npx hexo deploy`,部署由 GitHub Actions 完成。

---

## 🚀 GitHub Actions 自动部署

定义在 `.github/workflows/deploy.yml`,触发条件:

- 推送到 `dev` 分支(任意改动都会构建)
- 在 Actions 页手动点 **Run workflow**

工作流程:

```
push to dev
   ↓
Checkout → Node 20 → npm ci → hexo clean → hexo generate
   ↓
peaceiris/actions-gh-pages 把 ./public 推到 master
   ↓
GitHub Pages 自动重新部署
```

构建大约 **1 - 2 分钟**。

---

## 📁 目录结构

```
.
├── _config.yml              # Hexo 全局配置
├── _config.butterfly.yml    # Butterfly 主题配置(改外观主要看这个)
├── package.json             # Hexo 及插件依赖
├── scaffolds/               # 新建文章的模板
├── source/
│   ├── _posts/              # ✨ 文章在这里
│   ├── _data/               # 友链等数据
│   ├── about/               # "关于" 页
│   ├── images/              # 图片资源
│   └── ...                  # tags / categories / music / movies 页
├── themes/
│   └── Butterfly/           # 主题文件(已扁平化,可直接修改)
└── .github/workflows/
    └── deploy.yml           # 自动部署工作流
```

---

## ❓ 常见问题

**Q: push 到 dev 后博客没更新?**
A: 看 [Actions 页面](https://github.com/EternityLovehh/eternitylovehh.github.io/actions),如果 workflow 跑红了,点进去看哪一步报错。

**Q: 修改 `.github/workflows/*.yml` 推送被拒(`workflow scope`)?**
A: 你用的 PAT 需要勾选 `workflow` 权限:<https://github.com/settings/tokens> → 编辑 token → 勾上 `workflow`。

**Q: 想加一篇草稿,先不发布?**
A: 把文件放在 `source/_drafts/` 而不是 `_posts/`,Hexo 默认不会构建草稿。

**Q: 文章里的图片怎么放?**
A: `_config.yml` 里 `post_asset_folder: true` 已开启。在 `source/_posts/` 里和文章同名的文件夹放图片,Markdown 用相对路径引用即可。
