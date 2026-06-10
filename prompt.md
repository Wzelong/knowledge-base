# Prompts

## Prompt 1 — single-agent pipeline (single.PNG)

我在做一个个人的知识库。在backend做一个pipeline 参考这个：[single.PNG] 。用/Users/zelong/Documents/GitHub/knowledge-base/.claude/skills/openai-agent-sdk，写一个agent，用gpt-5.4-mini reasoning low，如果输出是文件比如pdf直接attach文件在agent的输入里，输出是我平时看的一些资料，先用/Users/zelong/Documents/GitHub/knowledge-base/data/transformer.txt做此阶段的测试。agent要把输入提取出summary和其中的核心concept，每个concept包括名字和描述，用structured output。输出后把每个concept（name+description）进行embedding，用openai的embedding模型，batch embedding。然后与数据库中已有的concept进行向量搜索rank 设定一个阀值，进行去重和融合。关于融合，在数据库中每个concept的description应该是一个list吗，这样可以把新的description加入进去，是否还要重新embedding，还是数据库中已有的获胜，或者让一个agent去重新写description？数据库中的每个concept需要有一个source list，每个source有metadata+提取出来的summary。因为我没有设置supabase，所以你把真实的数据库代码写出来，但是测试的时候mock一下。几个需要注意的地方，一个是去重阀值的设置，和提取concept的agent prompt，必须要是核心的concept，不能太宽泛，比如类似"ai","llm"这些都过于宽泛。你需要写完核心代码后，进行测试，来找到合适的阀值和有效的提示词，/Users/zelong/Documents/GitHub/knowledge-base/.claude/skills/writing-prompts，切记提示词要generalize，不要overfit。

## Prompt 2 — parallel fan-out + aggregator (multiple.PNG)

现在先测试这个pdf能不能跑得通：/Users/zelong/Documents/GitHub/knowledge-base/data/attention.pdf。然后我们要扩展目前的pipeline，参照这个图：[multiple.PNG] 。有时候一个文件/输入可能太大，要分成几部分，这样就让多个agent并行一起跑自己的部分，然后用一个aggregator agent去进行summary的总结和concept的去重和融合，然后再走embedding和与数据库对比和塞入。同样一定要好好写aggregator的提示词。

## Prompt 3 — tools, prompt optimization, stability and timing

现在让agent变得更加有能，让它获得一些有用的工具，比如web search和fetch link 比如说我如果提供一个link作为输入 agent应该能够尝试获得link里的内容。同时完成这个之后，进行整个pipeline的优化，主要集中在提示词，要求提示词清晰，不要overfit，同时进行稳定性测试，多次跑同一个文件看输出是否稳定，另外记录pipeline的处理时间，是否与输入的大小有关
