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

}