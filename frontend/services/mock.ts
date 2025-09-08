export const mockApiService = {
  async processDocumentation(request: { url: string }) {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    return {
      success: true,
      message: "Documentation processed successfully",
      script: "This is a mock documentation script for " + request.url,
      sections: ["Introduction", "Key Concepts", "Use Cases"],
    };
  },

  async sendChatMessage(request: {
    messages: Array<{ role: string; content: string }>;
  }) {
    // Simulate network delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    const lastMessage = request.messages[request.messages.length - 1];

    return {
      response: `This is a mock response to: "${lastMessage.content}"\n\nI'm a mock AI assistant helping you understand the documentation. Feel free to ask any questions!`,
      audio_url: null,
    };
  },
};
