# n8n LangChain Integration Guide

**Complete reference for using LangChain nodes in n8n workflows**

**Based on:** n8n Official Documentation (November 2025)

---

## 📚 Overview

n8n provides a comprehensive collection of LangChain nodes that implement LangChain's JavaScript framework functionality. These nodes are fully configurable and can be integrated with any other n8n nodes.

### Key Benefits

- ✅ **Visual LangChain Development** - Build AI workflows without code
- ✅ **Pre-configured Nodes** - Ready-to-use agents, chains, tools, and memory
- ✅ **Flexible Integration** - Connect LangChain with 400+ n8n integrations
- ✅ **Production-Ready** - Built-in error handling and observability

### What You Get

- **AI Agents** - Conversational, ReAct, OpenAI Functions, Plan & Execute, SQL, Tools agents
- **Chat Models** - OpenAI, Anthropic, Google Gemini, Mistral, Ollama, AWS Bedrock, Azure, and more
- **Memory Systems** - Simple, MongoDB, Redis, Postgres, Xata, Zep, Motorhead
- **Tools** - Calculator, Wikipedia, Wolfram Alpha, Custom API calls, Workflow execution
- **Vector Stores** - Pinecone, Qdrant, Supabase, in-memory stores
- **Chains** - Basic LLM, Q&A, Summarization, Information Extraction

---

## 🎯 Quick Start

### 1. Understanding n8n's LangChain Architecture

n8n implements LangChain using **Cluster Nodes** - a special node type with:

- **Root Node**: Main workflow node (Agent, Chain, etc.)
- **Sub-Nodes**: Connected components (LLM, Memory, Tools, etc.)

```
┌─────────────────────────────────────┐
│     AI Agent (Root Node)            │
│  ┌─────────────────────────────┐   │
│  │ OpenAI Chat Model           │   │
│  │ (Sub-node)                  │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ Simple Memory               │   │
│  │ (Sub-node)                  │   │
│  └─────────────────────────────┘   │
│  ┌─────────────────────────────┐   │
│  │ Wikipedia Tool              │   │
│  │ (Sub-node)                  │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

### 2. Creating Your First LangChain Workflow

**Example: Simple Chat Agent**

1. **Add Chat Trigger** → Triggers workflow from chat interface
2. **Add AI Agent node** → Main agent orchestrator
3. **Connect OpenAI Chat Model sub-node** → LLM for responses
4. **Connect Simple Memory sub-node** → Conversation history
5. **Add Respond to Chat** → Send response back to user

**Workflow Structure:**

```
Chat Trigger → AI Agent → Respond to Chat
                  ↓
            [OpenAI Model]
            [Simple Memory]
```

---

## 🧩 Core Components

### Trigger Nodes

| Node | Purpose | Use Case |
|------|---------|----------|
| **Chat Trigger** | Start workflow from chat | Conversational AI apps |
| **Webhook** | HTTP endpoint trigger | API-based AI services |
| **Schedule Trigger** | Run on schedule | Batch AI processing |
| **Manual Trigger** | Manual execution | Testing and debugging |

### Root Nodes (Main Workflow Nodes)

#### AI Agent

**Purpose:** Autonomous agents that can use tools and make decisions

**Agent Types:**

| Type | When to Use | Best For |
|------|-------------|----------|
| **Conversational Agent** | Multi-turn conversations | Chatbots, support agents |
| **ReAct Agent** | Reasoning + Acting pattern | Complex problem solving |
| **OpenAI Functions Agent** | OpenAI function calling | Structured tool usage |
| **Plan & Execute Agent** | Multi-step planning | Long-running tasks |
| **SQL Agent** | Database queries | Data analysis workflows |
| **Tools Agent** | Custom tool execution | Specialized automations |

**Example Configuration:**

```json
{
  "agent": "conversationalAgent",
  "model": "gpt-4-mini",
  "memory": "bufferMemory",
  "tools": ["wikipedia", "calculator"]
}
```

#### Basic LLM Chain

**Purpose:** Simple prompt → LLM → response

**Use Cases:**

- Text generation
- Content creation
- Simple Q&A
- Classification

#### Question & Answer Chain

**Purpose:** RAG (Retrieval-Augmented Generation) with vector stores

**Use Cases:**

- Document Q&A
- Knowledge base search
- Context-aware responses

#### Summarization Chain

**Purpose:** Text summarization with various strategies

**Strategies:**

- Map-Reduce
- Refine
- Stuff (single prompt)

---

## 🤖 Chat Models (LLMs)

### Available Models

| Provider | Node Name | Key Features |
|----------|-----------|--------------|
| **OpenAI** | OpenAI Chat Model | GPT-4, GPT-3.5-turbo, streaming |
| **Anthropic** | Anthropic Chat Model | Claude 3 Opus, Sonnet, Haiku |
| **Google** | Google Gemini Chat Model | Gemini 1.5 Pro, Flash |
| **Mistral** | Mistral Cloud Chat Model | Mixtral, fast inference |
| **Ollama** | Ollama Chat Model | Local models, privacy |
| **AWS Bedrock** | AWS Bedrock Chat Model | Enterprise cloud LLMs |
| **Azure** | Azure OpenAI Chat Model | Azure-hosted OpenAI |
| **Groq** | Groq Chat Model | Extremely fast inference |
| **DeepSeek** | DeepSeek Chat Model | Chinese models |

### Model Selection Tips

**For Production:**

- **High Quality:** GPT-4, Claude 3 Opus, Gemini 1.5 Pro
- **Balanced:** GPT-4-mini, Claude 3 Sonnet, Gemini 1.5 Flash
- **Fast/Cheap:** GPT-3.5-turbo, Claude 3 Haiku, Mistral Small

**For Self-Hosted:**

- **Ollama:** Llama 3, Mistral, Phi-3 (privacy + zero cost)

---

## 💾 Memory Systems

### Memory Types

| Memory Type | Storage | Best For |
|------------|---------|----------|
| **Simple Memory** | In-memory | Testing, simple conversations |
| **MongoDB Chat Memory** | MongoDB | Production chat apps |
| **Redis Chat Memory** | Redis | High-performance, distributed |
| **Postgres Chat Memory** | PostgreSQL | SQL-based apps |
| **Xata** | Xata service | Serverless apps |
| **Zep** | Zep service | Advanced memory features |
| **Motorhead** | Motorhead service | Managed memory |

### Memory Configuration Example

```json
{
  "memory": "redisChat",
  "config": {
    "sessionIdTemplate": "{{$json.userId}}",
    "contextWindowLength": 10,
    "redisUrl": "redis://localhost:6379"
  }
}
```

**Key Concepts:**

- **Session ID:** Unique identifier per conversation
- **Context Window:** Number of messages to remember
- **Persistence:** Where conversation history is stored

---

## 🛠️ Tools

### Built-in Tools

| Tool | Purpose | Example Use |
|------|---------|-------------|
| **Calculator** | Math operations | "What's 15% of $450?" |
| **Wikipedia** | Knowledge lookup | "Tell me about quantum computing" |
| **Wolfram Alpha** | Computational knowledge | "Distance from Earth to Mars" |
| **Custom API** | External APIs | Weather, stocks, custom data |
| **n8n Workflow** | Call other workflows | Multi-step automations |
| **Code Interpreter** | Execute Python | Data analysis, transformations |

### Creating Custom Tools

**Example: Weather API Tool**

1. **Add HTTP Request node** → Configure API call
2. **Wrap in "Call n8n Workflow Tool"** → Make it usable by agent
3. **Configure tool description** → How agent should use it

```json
{
  "name": "get_weather",
  "description": "Get current weather for a city. Input should be city name.",
  "workflowId": "weather-workflow-123"
}
```

---

## 📊 Vector Stores & Embeddings

### Vector Store Nodes

| Vector Store | Best For |
|--------------|----------|
| **Pinecone** | Production, scalability |
| **Qdrant** | Self-hosted, privacy |
| **Supabase** | PostgreSQL-based |
| **In-Memory** | Testing, small datasets |
| **Chroma** | Local development |

### Embedding Models

| Provider | Model |
|----------|-------|
| **OpenAI** | text-embedding-3-small, text-embedding-3-large |
| **Google** | Google Vertex, Google Gemini embeddings |
| **Ollama** | Local embedding models |
| **HuggingFace** | Open-source models |
| **Mistral** | Mistral embeddings |

### RAG Workflow Pattern

```
Document → Split Text → Generate Embeddings → Store in Vector DB
                                                      ↓
User Query → Generate Query Embedding → Similarity Search → Retrieve Context
                                                              ↓
                                              Context + Query → LLM → Answer
```

---

## 🔗 Integration with n8n Workflows

### Combining LangChain with n8n Nodes

**Example: GitHub Issue Analyzer**

```
GitHub Trigger → Get Issue Details → AI Agent (analyze sentiment)
                                        ↓
                              Google Gemini Model
                                        ↓
                    Slack → Post Analysis Results
```

**Example: Customer Support Automation**

```
Email Trigger → Extract Customer Query → Question & Answer Chain
                                              ↓
                                        Vector Store (FAQ)
                                              ↓
                                        OpenAI Model
                                              ↓
                              Send Email Response
```

---

## 🎨 Common Patterns

### Pattern 1: Conversational Chatbot

**Components:**

- Chat Trigger
- AI Agent (Conversational)
- OpenAI Chat Model
- Redis Chat Memory
- Respond to Chat

**Features:**

- Multi-turn conversations
- Persistent memory
- Context-aware responses

### Pattern 2: RAG Document Q&A

**Components:**

- Manual Trigger (for indexing)
- Read Binary Files
- Recursive Character Text Splitter
- OpenAI Embeddings
- Pinecone Vector Store
- Question & Answer Chain

**Workflow:**

1. **Indexing:** Load docs → Split → Embed → Store
2. **Query:** User question → Retrieve context → Generate answer

### Pattern 3: AI-Powered Workflow Automation

**Components:**

- Schedule Trigger
- AI Agent (Plan & Execute)
- Multiple Custom Tools (API calls, database queries)
- Slack notification

**Use Case:** Daily report generation with AI analysis

### Pattern 4: Multi-Model Ensemble

**Components:**

- Webhook Trigger
- 3x AI Agents (GPT-4, Claude, Gemini)
- Merge node
- Final AI Agent (synthesizer)

**Benefit:** Combine strengths of different models

---

## 📈 Best Practices

### 1. Prompt Engineering

**Good Prompts:**

- Clear instructions
- Examples (few-shot learning)
- Output format specification
- Role definition

**Example:**

```
You are a helpful customer support agent.
Analyze the customer's message and:
1. Classify the urgency (low/medium/high)
2. Identify the main issue
3. Suggest a resolution

Customer message: {{$json.message}}

Respond in JSON format:
{
  "urgency": "...",
  "issue": "...",
  "resolution": "..."
}
```

### 2. Memory Management

**Tips:**

- Use session IDs to separate conversations
- Set appropriate context window lengths
- Clear old sessions periodically
- Use persistent storage for production

### 3. Tool Design

**Principles:**

- Clear, descriptive names
- Precise descriptions
- Handle errors gracefully
- Return structured data

### 4. Vector Store Optimization

**Tips:**

- Choose chunk size carefully (typically 500-1000 tokens)
- Use overlap between chunks
- Index with metadata for filtering
- Monitor retrieval quality

### 5. Cost Optimization

**Strategies:**

- Use cheaper models for simple tasks (GPT-4-mini vs GPT-4)
- Cache responses when appropriate
- Set max token limits
- Use Ollama for development

### 6. Error Handling

**Implement:**

- Fallback models
- Timeout configurations
- Retry logic with exponential backoff
- User-friendly error messages

---

## 🔍 Debugging & Monitoring

### Built-in Debugging

**n8n provides:**

- Execution history
- Node-level outputs
- Error messages
- Token usage tracking

### LangSmith Integration (Self-Hosted Only)

**Setup:**

1. Create LangSmith account
2. Get API key
3. Configure environment variables:

   ```bash
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your-key-here
   LANGCHAIN_PROJECT=your-project-name
   ```

**Benefits:**

- Trace complete LangChain execution
- Monitor LLM calls
- Debug agent decisions
- Analyze performance

---

## 💡 Real-World Examples

### Example 1: Customer Support Bot

**Workflow:**

```
Slack Event Trigger
  ↓
AI Agent (Conversational)
  ├─ OpenAI GPT-4-mini
  ├─ MongoDB Chat Memory
  ├─ Wikipedia Tool (for product info)
  └─ Custom API Tool (customer database)
  ↓
Slack Reply
```

**Features:**

- Remembers conversation context
- Looks up product information
- Checks customer order history
- Escalates to human when needed

### Example 2: Content Creation Pipeline

**Workflow:**

```
Schedule Trigger (daily)
  ↓
Airtable (get topics)
  ↓
Basic LLM Chain (generate outline)
  ↓
Loop over outline sections
  ↓
Basic LLM Chain (write section)
  ↓
Summarization Chain (create summary)
  ↓
Google Docs (create document)
```

### Example 3: Intelligent Email Router

**Workflow:**

```
Email Trigger
  ↓
Text Classifier (classify intent)
  ↓
Switch Node
  ├─ Sales → CRM update
  ├─ Support → Ticket creation
  ├─ Feedback → Sentiment analysis
  └─ Other → Manual review queue
```

---

## 🚀 Advanced Topics

### Custom LangChain Code

**Use the "LangChain Code" node** for custom LangChain logic:

```javascript
const { ChatOpenAI } = require("@langchain/openai");
const { PromptTemplate } = require("@langchain/core/prompts");

const model = new ChatOpenAI({
  modelName: "gpt-4-mini",
  temperature: 0.7
});

const prompt = PromptTemplate.fromTemplate(
  "Translate {text} to {language}"
);

const chain = prompt.pipe(model);

const result = await chain.invoke({
  text: $input.first().json.text,
  language: $input.first().json.language
});

return { translation: result.content };
```

### Streaming Responses

**Supported by:**

- OpenAI Chat Model
- Anthropic Chat Model
- Most modern LLM providers

**Enable in node settings:**

```json
{
  "streaming": true
}
```

**Handle in workflow:**

- Use "Respond to Chat" node
- Tokens stream as they're generated

### Function Calling

**OpenAI Functions Agent** enables structured tool calls:

```json
{
  "function": {
    "name": "get_user_data",
    "description": "Retrieve user information",
    "parameters": {
      "type": "object",
      "properties": {
        "userId": {
          "type": "string",
          "description": "The user's ID"
        }
      }
    }
  }
}
```

---

## 📖 Learning Resources

### Official Documentation

- **n8n LangChain Docs:** <https://docs.n8n.io/advanced-ai/langchain/>
- **LangChain JS Docs:** <https://js.langchain.com/docs/>
- **LangChain Cookbook:** <https://github.com/langchain-ai/langchain/tree/master/cookbook>

### Tutorials

- **n8n Video Courses:** <https://docs.n8n.io/video-courses/>
- **LangChain Learning:** <https://docs.n8n.io/advanced-ai/langchain/langchain-learning-resources/>

### Key Concepts to Understand

1. **Agents vs Chains:** When to use which
2. **Memory:** How conversation context works
3. **Tools:** Extending agent capabilities
4. **Vector Stores:** RAG fundamentals
5. **Embeddings:** Semantic search basics

---

## 🛡️ Security & Privacy

### Best Practices

1. **API Keys:**
   - Store in n8n credentials
   - Never hardcode in workflows
   - Rotate regularly

2. **Data Privacy:**
   - Use Ollama for sensitive data
   - Consider self-hosted vector stores
   - Review LLM provider data policies

3. **Access Control:**
   - Restrict workflow execution permissions
   - Use webhook authentication
   - Monitor execution logs

4. **PII Handling:**
   - Redact sensitive information
   - Use anonymization where possible
   - Comply with GDPR/privacy regulations

---

## 🔧 Troubleshooting

### Common Issues

**Issue:** "Model not found" error

**Solution:** Verify API key and model name match provider

---

**Issue:** Memory not persisting

**Solution:** Check session ID is correctly set and memory service is running

---

**Issue:** Agent not using tools

**Solution:** Improve tool descriptions, ensure agent type supports tools

---

**Issue:** High latency

**Solution:** Use faster models (GPT-4-mini, Claude Haiku), reduce context window

---

**Issue:** Vector search returns irrelevant results

**Solution:** Adjust chunk size, improve embedding model, add metadata filters

---

## 📊 Performance Optimization

### Response Time

- **Use streaming** for perceived performance
- **Cache responses** for repeated queries
- **Choose faster models** for simple tasks
- **Parallel execution** where possible

### Token Usage

- **Monitor token consumption** via execution logs
- **Set max_tokens** limits
- **Use shorter system prompts**
- **Truncate long inputs** appropriately

### Cost Management

| Model Tier | Use Case | Example |
|------------|----------|---------|
| **Premium** | Complex reasoning, critical quality | GPT-4, Claude 3 Opus |
| **Balanced** | Production apps, good quality | GPT-4-mini, Claude 3 Sonnet |
| **Fast** | High volume, simple tasks | GPT-3.5-turbo, Gemini Flash |
| **Self-Hosted** | Development, privacy, zero cost | Ollama (Llama 3, Mistral) |

---

## 🎯 Next Steps

### 1. Build Your First Workflow

Start with a simple chatbot:

- Chat Trigger
- AI Agent (Conversational)
- OpenAI Chat Model
- Simple Memory
- Respond to Chat

### 2. Add Tools

Extend with Wikipedia or Calculator tools

### 3. Implement RAG

Create a document Q&A system with vector store

### 4. Production Deployment

- Add error handling
- Configure persistent memory
- Set up monitoring
- Optimize costs

### 5. Advanced Patterns

- Multi-agent collaboration
- Streaming responses
- Custom tool creation
- LangSmith integration

---

## 📞 Support & Community

- **n8n Community Forum:** <https://community.n8n.io/>
- **Discord:** <https://discord.gg/n8n>
- **GitHub Issues:** <https://github.com/n8n-io/n8n/issues>
- **LangChain Discord:** <https://discord.gg/langchain>

---

**Last Updated:** November 9, 2025
**Version:** n8n 1.x with LangChain.js integration
**Maintained by:** TTA.dev Team (based on n8n official docs)


---
**Logseq:** [[TTA.dev/Apps/N8n/N8n_langchain_integration_guide]]
