# 贡献指南

感谢您对Paper Agent项目的关注！我们欢迎任何形式的贡献，包括但不限于代码提交、文档改进、问题报告和功能建议。

## 开发环境设置

### 克隆仓库
```bash
git clone https://github.com/yourusername/paper-agent.git
cd paper-agent
```

### 安装依赖

#### 后端依赖
```bash
# 使用uv（推荐）
pip install uv
uv venv
source .venv/bin/activate  # Linux/Mac
# 或 .venv\Scripts\activate  # Windows
uv pip install -r requirements.txt

# 或使用传统pip
pip install -r requirements.txt
```

#### 前端依赖
```bash
cd frontend
npm install
```

### 创建配置文件
复制并修改配置文件：
```bash
cp config/config.yaml.example config/config.yaml
```

## 代码规范

### Python代码规范
- 遵循PEP 8代码风格
- 使用类型提示
- 保持函数和方法的简洁性
- 编写适当的文档字符串

### JavaScript/React规范
- 遵循ESLint规则
- 使用函数式组件和Hooks
- 保持组件的单一职责
- 适当使用PropTypes或TypeScript

### Git提交规范
- 使用清晰的提交信息
- 遵循[约定式提交](https://www.conventionalcommits.org/zh-hans/v1.0.0/)规范
- 每个提交应该只解决一个问题

## 开发流程

1. Fork项目仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 代码结构

```
paper_agent/
├── backend/                 # 后端服务
│   ├── api/                 # API路由
│   ├── models/              # 数据模型
│   ├── services/            # 业务逻辑
│   ├── config/              # 配置管理
│   └── main.py              # 应用入口
├── frontend/                # 前端应用
│   ├── public/              # 静态资源
│   ├── src/                 # 源代码
│   │   ├── components/      # React组件
│   │   ├── pages/           # 页面组件
│   │   ├── services/        # API服务
│   │   └── App.js           # 主应用组件
├── paper_agent/             # 核心模块
├── config/                  # 配置文件
├── data/                    # 数据存储
├── tests/                   # 测试文件
├── requirements.txt         # Python依赖
└── README.md               # 项目说明
```

## 添加新的LLM提供商

1. 在[backend/services/llm_service.py](file:///Users/kingdeguo/Downloads/同步空间/codes/paper_agent/paper_agent/backend/services/llm_service.py)中创建新的提供商类，继承[LLMProvider](file:///Users/kingdeguo/Downloads/同步空间/codes/paper_agent/paper_agent/backend/services/llm_service.py#L12-L20)抽象类
2. 实现以下方法：
   - `generate_summary`
   - `generate_response`
   - `generate_streaming_response`
3. 在[LLMService](file:///Users/kingdeguo/Downloads/同步空间/codes/paper_agent/paper_agent/backend/services/llm_service.py#L385-L465)的`_create_provider`方法中添加新的提供商
4. 更新配置文件支持和文档

## 测试

### 后端测试
```bash
cd backend
python -m pytest tests/
```

### 前端测试
```bash
cd frontend
npm test
```

## 报告问题

如果您发现了问题，请在GitHub上创建Issue，并包含以下信息：
- 问题的清晰描述
- 重现步骤
- 预期行为和实际行为
- 环境信息（操作系统、Python版本等）
- 相关日志或截图

## 提交Pull Request

1. 确保您的代码符合项目规范
2. 添加适当的测试用例
3. 更新相关文档
4. 确保所有测试通过
5. 提交PR并详细描述变更内容

## 问题和讨论

如果您有任何问题或建议，欢迎在GitHub Issues中提出讨论。

再次感谢您的贡献！