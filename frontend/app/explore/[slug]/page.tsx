import axios from "axios";

export default async function Explore({ params }: { params: Promise<{ slug: number }> }) {

    const { slug } = await params;
    let agent = null;
    try {
        agent = (await axios.get(`http://localhost:8000/api/agents/${slug}`)).data;
    }
    catch {}

    return (
        <div className="w-full relative pt-[100px]">
            {
                agent == null ?
                <div className="mx-auto w-fit text-[40px] text-center sm:text-[60px] text-white">
                    <div>Agent not found.</div>
                    <div className="text-sm">Agent with id <span className="font-bold">{slug}</span> does not exist.</div>
                </div>
                    :
                <>
                    <div className="mx-auto w-fit text-[40px] sm:text-[60px] text-white">
                        <div>{agent.title}</div>
                    </div>
                    <div className="max-w-5xl mx-auto px-6 pb-[150px]">
                        <div className="bg-white/90 backdrop-blur-md rounded-2xl mt-[45px] shadow-xl/10 py-6 px-8">

                        </div>
                    </div>
                </>
            }
        </div>
    );  
}