# Continue Extension: Exact Streaming Message Execution Path

## COMPLETE FLOW: From `streamSse()` to Final Message

### 1. ENTRY POINT: `llmStreamChat()` - [core/llm/streamChat.ts](https://github.com/continuedev/continue/blob/main/core/llm/streamChat.ts)

**Consumer code that calls the LLM streaming:**

```typescript
export async function* llmStreamChat(
  configHandler: ConfigHandler,
  abortController: AbortController,
  msg: Message<ToCoreProtocol["llm/streamChat"][0]>,
  ide: IDE,
  messenger: IMessenger<ToCoreProtocol, FromCoreProtocol>,
): AsyncGenerator<ChatMessage, PromptLog> {
  const { config } = await configHandler.loadConfig();
  if (!config) {
    throw new Error("Config not loaded");
  }

  const {
    legacySlashCommandData,
    completionOptions,
    messages,
    messageOptions,
  } = msg.data;

  const model = config.selectedModelByRole.chat;

  if (!model) {
    throw new Error("No chat model selected");
  }

  // ... error handling setup ...

  try {
    if (legacySlashCommandData) {
      // ... slash command handling ...
    } else {
      // ✅ MAIN FLOW: Call model.streamChat()
      const gen = model.streamChat(
        messages,
        abortController.signal,
        completionOptions,
        messageOptions,
      );
      
      // ✅ GENERATOR CONSUMER LOOP - Manual iteration over async generator
      let next = await gen.next();
      while (!next.done) {
        if (abortController.signal.aborted) {
          next = await gen.return(errorPromptLog);
          break;
        }

        // ✅ YIELDS individual ChatMessage chunks
        const chunk = next.value;

        yield chunk;  // <- Forward to caller
        next = await gen.next();
      }
      
      // ✅ FINAL: Return the PromptLog (generator return value)
      if (!next.done) {
        throw new Error("Will never happen");
      }

      return next.value;
    }
  } catch (error) {
    throw error;
  }
}
```

**WHAT HAPPENS WHEN STREAM YIELDS NOTHING:**
- If the generator never yields (empty stream), the `while (!next.done)` loop exits immediately
- `next.value` still contains the `PromptLog` return value
- Stream is marked complete even if no chunks were yielded

---

### 2. ORCHESTRATION: `BaseLLM.streamChat()` - [core/llm/index.ts](https://github.com/continuedev/continue/blob/main/core/llm/index.ts#L1170-L1272)

**Main streaming entry point that accumulates chunks:**

```typescript
async *streamChat(
  _messages: ChatMessage[],
  signal: AbortSignal,
  options: LLMFullCompletionOptions = {},
  messageOptions?: MessageOption,
): AsyncGenerator<ChatMessage, PromptLog> {
  this.lastRequestId = undefined;

  let { completionOptions, logEnabled } =
    this._parseCompletionOptions(options);

  const interaction = logEnabled
    ? this.logger?.createInteractionLog()
    : undefined;
  let status: InteractionStatus = "in_progress";

  // ... message compilation ...

  const thinking: string[] = [];
  const completion: string[] = [];  // ✅ ACCUMULATION ARRAYS
  let usage: Usage | undefined = undefined;
  let citations: null | string[] = null;

  try {
    if (this.templateMessages) {
      // Non-OpenAI path: _streamComplete
      for await (const chunk of this._streamComplete(
        prompt,
        signal,
        completionOptions,
      )) {
        completion.push(chunk);
        interaction?.logItem({
          kind: "chunk",
          chunk: chunk,
        });
        yield { role: "assistant", content: chunk };
      }
    } else {
      if (this.shouldUseOpenAIAdapter("streamChat") && this.openaiAdapter) {
        // ✅ OpenAI/adapter path
        let body = toChatBody(messages, completionOptions, {
          includeReasoningField: this.supportsReasoningField,
          includeReasoningDetailsField: this.supportsReasoningDetailsField,
          includeReasoningContentField: this.supportsReasoningContentField,
        });
        body = this.modifyChatBody(body);

        const canUseResponses = this.canUseOpenAIResponses(completionOptions);
        const useStream = completionOptions.stream !== false;

        let iterable: AsyncIterable<ChatMessage>;
        if (canUseResponses) {
          iterable = useStream
            ? this.responsesStream(messages, signal, completionOptions)
            : this.responsesNonStream(messages, signal, completionOptions);
        } else {
          iterable = useStream
            ? this.openAIAdapterStream(body, signal, (c) => {
                if (!citations) {
                  citations = c;
                }
              })
            : this.openAIAdapterNonStream(body, signal);
        }

        // ✅ CONSUMER LOOP: Iterate over chunks from adapter
        for await (const chunk of iterable) {
          // ✅ CHUNK PROCESSING: Convert raw chunks to ChatMessage
          const result = this.processChatChunk(chunk, interaction);
          
          // ✅ ACCUMULATE into arrays
          completion.push(...result.completion);
          thinking.push(...result.thinking);
          if (result.usage !== null) {
            usage = result.usage;
          }
          
          // ✅ YIELD to consumer (llmStreamChat)
          yield result.chunk;
        }
      } else {
        // Direct provider path: _streamChat
        for await (const chunk of this._streamChat(
          messages,
          signal,
          completionOptions,
        )) {
          const result = this.processChatChunk(chunk, interaction);
          completion.push(...result.completion);
          thinking.push(...result.thinking);
          if (result.usage !== null) {
            usage = result.usage;
          }
          yield result.chunk;
        }
      }
    }

    // ✅ COMPLETION LOGGING
    status = this._logEnd(
      completionOptions.model,
      prompt,
      completion.join(""),  // ✅ FINAL MESSAGE: concatenate accumulated chunks
      thinking.join(""),
      interaction,
      usage,
    );
  } catch (e) {
    // ... error logging ...
    throw e;
  } finally {
    if (status === "in_progress") {
      this._logEnd(
        completionOptions.model,
        prompt,
        completion.join(""),
        undefined,
        interaction,
        usage,
        "cancel",
      );
    }
  }

  // ✅ RETURN: Generator returns PromptLog
  return {
    modelTitle: this.title ?? completionOptions.model,
    modelProvider: this.underlyingProviderName,
    prompt,
    completion: completion.join(""),
  };
}
```

**KEY PROCESSING: `processChatChunk()`**

```typescript
private processChatChunk(
  chunk: ChatMessage,
  interaction: ILLMInteractionLog | undefined,
): {
  completion: string[];
  thinking: string[];
  usage: Usage | null;
  chunk: ChatMessage;
} {
  const completion: string[] = [];
  const thinking: string[] = [];
  let usage: Usage | null = null;

  if (chunk.role === "assistant") {
    // ✅ Extract text from assistant message
    completion.push(this._formatChatMessage(chunk));
  } else if (chunk.role === "thinking" &&
    typeof chunk.content === "string") {
    thinking.push(chunk.content);
  }

  interaction?.logItem({
    kind: "message",
    message: chunk,
  });

  if (chunk.role === "assistant" && chunk.usage) {
    usage = chunk.usage;
  }

  // ✅ Return accumulation arrays + original chunk
  return {
    completion,
    thinking,
    usage,
    chunk,
  };
}
```

---

### 3. OPENAI ADAPTER STREAMING: `openAIAdapterStream()` - [core/llm/index.ts](https://github.com/continuedev/continue/blob/main/core/llm/index.ts#L1031-L1053)

**Converts raw OpenAI chunks to ChatMessage:**

```typescript
private async *openAIAdapterStream(
  body: ChatCompletionCreateParams,
  signal: AbortSignal,
  onCitations: (c: string[]) => void,
): AsyncGenerator<ChatMessage> {
  const stream = this.openaiAdapter!.chatCompletionStream(
    { ...body, stream: true },
    signal,
  );
  
  // ✅ ITERATE over ChatCompletionChunk stream
  for await (const chunk of stream) {
    if (!this.lastRequestId && typeof (chunk as any).id === "string") {
      this.lastRequestId = (chunk as any).id;
    }
    
    // ✅ CONVERT ChatCompletionChunk → ChatMessage
    const chatChunk = fromChatCompletionChunk(chunk as any);
    if (chatChunk) {
      yield chatChunk;  // ✅ Yield converted ChatMessage
    }
    
    if ((chunk as any).citations && Array.isArray((chunk as any).citations)) {
      onCitations((chunk as any).citations);
    }
  }
}
```

---

### 4. LLAMA HANDLER (Direct Provider): `OpenAI._streamChat()` - [core/llm/llms/OpenAI.ts](https://github.com/continuedev/continue/blob/main/core/llm/llms/OpenAI.ts#L519-L567)

**Direct streaming from HTTP response with `streamSse()`:**

```typescript
protected async *_streamChat(
  messages: ChatMessage[],
  signal: AbortSignal,
  options: CompletionOptions,
): AsyncGenerator<ChatMessage> {
  if (
    !isChatOnlyModel(options.model) &&
    this.supportsCompletions() &&
    (NON_CHAT_MODELS.includes(options.model) ||
      this.useLegacyCompletionsEndpoint ||
      options.raw)
  ) {
    for await (const content of this._legacystreamComplete(
      renderChatMessage(messages[messages.length - 1]),
      signal,
      options,
    )) {
      yield {
        role: "assistant",
        content,
      };
    }
    return;
  }

  const body = this._convertArgs(options, messages);

  const response = await this.fetch(this._getEndpoint("chat/completions"), {
    method: "POST",
    headers: this._getHeaders(),
    body: JSON.stringify({
      ...body,
      ...this.extraBodyProperties(),
    }),
    signal,
  });

  // Handle non-streaming response
  if (body.stream === false) {
    if (response.status === 499) {
      return; // Aborted by user
    }
    const data = await response.json();
    yield data.choices[0].message;
    return;
  }

  // ✅ STREAMING PATH: Consume SSE stream
  for await (const value of streamSse(response)) {
    // ✅ CONVERT: ChatCompletionChunk (SSE payload) → ChatMessage
    const chunk = fromChatCompletionChunk(value);
    
    // ✅ YIELD undefined if no content, otherwise yield chunk
    if (chunk) {
      yield chunk;
    }
  }
  
  // ✅ COMPLETION: Generator ends when streamSse() ends
  // (either [DONE] marker or connection close)
}
```

---

### 5. SSE STREAMING: `streamSse()` - [@continuedev/fetch](https://github.com/continuedev/continue/blob/main/packages/fetch/src/stream.ts)

**Low-level SSE event parsing:**

```typescript
export async function* streamSse(
  response: Response,
): AsyncGenerator<any> {
  // Parses Server-Sent Events format:
  // data: {"choices":[{"delta":{"content":"hello"}}]}
  // data: [DONE]
  
  for await (const line of streamLines(response)) {
    if (line.startsWith("data: ")) {
      const data = line.slice(6); // Remove "data: " prefix
      
      if (data === "[DONE]") {
        // ✅ STREAM ENDS: [DONE] marker received
        return;
      }
      
      try {
        // ✅ YIELD: Parsed JSON chunk
        yield JSON.parse(data);
      } catch {
        // Ignore malformed JSON
      }
    }
  }
  
  // ✅ STREAM ENDS: Connection closed or no more data
}
```

---

### 6. CHUNK CONVERSION: `fromChatCompletionChunk()` - [core/llm/openaiTypeConverters.ts](https://github.com/continuedev/continue/blob/main/core/llm/openaiTypeConverters.ts#L214-L494)

**Maps OpenAI chunks to Continue's ChatMessage format:**

```typescript
export function fromChatCompletionChunk(
  chunk: ChatCompletionChunk,
): ChatMessage | undefined {
  // Returns undefined if no content in this chunk
  
  if (!chunk.choices || chunk.choices.length === 0) {
    return undefined;  // ✅ EMPTY CHUNK: No choices
  }

  const choice = chunk.choices[0];
  
  if (!choice.delta) {
    return undefined;  // ✅ NO DELTA: Not a streaming chunk
  }

  const delta = choice.delta;

  // Handle text content
  if (delta.content) {
    return {
      role: "assistant",
      content: delta.content,  // ✅ EXTRACT TEXT DELTA
    };
  }

  // Handle tool calls
  if (delta.tool_calls) {
    return {
      role: "assistant",
      content: "",
      toolCalls: delta.tool_calls,  // ✅ EXTRACT TOOL CALLS
    };
  }

  // ✅ NO CONTENT: Return undefined (will be filtered out)
  return undefined;
}
```

---

## EXECUTION FLOW DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CONSUMER: llmStreamChat()                                    │
│    Receives: ChatMessage[], PromptLog (on completion)           │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   │ calls model.streamChat()
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. ORCHESTRATOR: BaseLLM.streamChat()                           │
│    Accumulates: completion[], thinking[], usage                 │
│    Yields: ChatMessage chunks (one per iteration)              │
└──────────────────┬──────────────────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│ 3a. ADAPTER      │  │ 3b. DIRECT       │
│ openAIAdapter    │  │ _streamChat()    │
│ Stream()         │  │ Stream()         │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         ▼                     ▼
┌──────────────────────────────────────────────────────────────────┐
│ 4. CONVERSION: fromChatCompletionChunk()                         │
│    Input:  ChatCompletionChunk (OpenAI format)                  │
│    Output: ChatMessage | undefined                              │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   │ (if content exists)
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ 5. PROCESSING: processChatChunk()                               │
│    Input:  ChatMessage chunk                                    │
│    Output: {completion[], thinking[], chunk}                    │
└──────────────────┬───────────────────────────────────────────────┘
                   │
                   │ (accumulate + yield)
                   ▼
┌──────────────────────────────────────────────────────────────────┐
│ 6. CONSUMER LOOP BACK TO llmStreamChat()                         │
│    Yields: chunk ──┐                                             │
│    Final: PromptLog with completion.join("")                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## WHEN STREAM YIELDS UNDEFINED / NO CHUNKS

### Scenario 1: Empty Choices Array
```typescript
// OpenAI sends: {"choices":[]}
// fromChatCompletionChunk() returns: undefined
// Result: Chunk is skipped (if (chunk) { yield chunk; })
```

### Scenario 2: Delta with no content
```typescript
// OpenAI sends: {"choices":[{"delta":{"role":"assistant"}}]}
// No delta.content, no delta.tool_calls
// fromChatCompletionChunk() returns: undefined
// Result: Chunk is skipped
```

### Scenario 3: [DONE] Marker
```typescript
// Server sends: data: [DONE]
// streamSse() returns (ends generator)
// No more yields
// Completion accumulates whatever was received
// Generator completes with PromptLog
```

### Scenario 4: Empty Stream (No Chunks Ever Sent)
```typescript
// Connection closes immediately or sends [DONE] right away
// completion[] remains []
// completion.join("") = ""
// PromptLog returns with empty completion
// Status: "success" (no error thrown)
```

---

## KEY CODE PATTERNS TO FIND IN CONTINUE

| Pattern | Files | Purpose |
|---------|-------|---------|
| `for await (const chunk of iterable) { yield result.chunk; }` | `index.ts:1217+` | Main accumulation loop |
| `completion.push(...result.completion)` | `index.ts:1256` | String concatenation O(n) → O(1) |
| `completion.join("")` | `index.ts:1301` | Final message construction |
| `for await (const value of streamSse(response)) { const chunk = fromChatCompletionChunk(value); if (chunk) { yield chunk; } }` | `OpenAI.ts:549-567` | Raw streaming handler |
| `if (chunk) { yield chunk; }` | Multiple files | Undefined chunk filtering |
| `let next = await gen.next(); while (!next.done) { yield next.value; next = await gen.next(); }` | `streamChat.ts:97-130` | Consumer loop pattern |
| `return { completion: completion.join(""), ... }` | `index.ts:1298-1302` | PromptLog with final message |

---

## WHAT HAPPENS WHEN UNDEFINED IS YIELDED

**At each level:**

1. **OpenAI._streamChat()**: `if (chunk) { yield chunk; }` → undefined is NOT yielded
2. **openAIAdapterStream()**: `if (chatChunk) { yield chatChunk; }` → undefined is NOT yielded
3. **BaseLLM.streamChat()**: Loop continues, `processChatChunk()` still called
   - `processChatChunk(undefined)` would crash → Never happens (filtered above)
4. **Consumer loop**: `for await (const chunk of iterable)` → undefined never received

**Result:** Undefined chunks are silently filtered at the source. No special handling needed in consumers.

---

## PROMISE RESOLUTION

**Generator Completion Triggers:**

1. **SSE `[DONE]`**: `streamSse()` returns
2. **Connection close**: Loop breaks
3. **Error thrown**: Propagates up
4. **Explicit return**: `return PromptLog`

**Promise chain:**
```
streamChat (AsyncGenerator) 
  → yields ChatMessage chunks during iteration
  → returns PromptLog when done (via next.value in consumer)
  → Consumer can use return value via return statement or .return()
```

---

## EMPTY STREAM BEHAVIOR

```typescript
// If stream sends [DONE] immediately:
for await (const value of streamSse(response)) {
  // Loop never executes (immediately returns on [DONE])
}

// completion[] stays empty
const result = { completion: completion.join("") }; // = ""

// Generator completes successfully
return result; // PromptLog with empty completion
```

**Status:** Still marked as "success" - empty responses are valid.

