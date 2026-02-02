export { }

declare global {

    type Query =
        {
            type: "text",
            text: string
        }
        | {
            type: "image",
            data: string,
            media_type: string
        }
        | {
            type: "document",
            data: string
        }
        | {
            type: "misc",
            data: string, 
            filename: string,
        }
    

    type Agent = {
        title: string,
        description: string,
        tools: Record<string, string>,
        cost_per_token: number,
        creator: string,
        id: string,
        private: boolean,
        date: string
    }
}