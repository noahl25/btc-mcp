# btc-mcp

An online platform for creators to launch MCP servers and earn Bitcoin.

AI agents can interact with each other and exchange payments, with access and transactions powered by Lightspark/Bitcoin, including L402-style paywall semantics. Passwordless authentication via the LNURL protocol is used for verifying creators' identity. 

The platform uses MCP (FastMCP) to standardize agent and tool interfaces, enabling seamless agent-to-agent interactions. Redis manages caching and ephemeral state for Lightning authentication and Docker provides isolated, deployable environments for MCP servers.

Access the MCP network by simply connecting your Lightspark node to a Python client, allowing your agent to use tools and make automatic payments without human intervention. Creators earn for every input and output token processed by their server.
