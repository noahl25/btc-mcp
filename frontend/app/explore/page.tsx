import AgentView from "@/components/AgentView";
import testData from "./testData.json"


export default function Explore() {

    const agents = testData as unknown as Agent[];

    return (
        <div className="w-full relative pt-[100px]">
            <div className="mx-auto w-fit text-[40px] sm:text-[60px] text-white">
                <div>Explore agents.</div>
            </div>
            <div className="max-w-5xl mx-auto px-6 pb-[150px]">
                <div className="bg-white/90 backdrop-blur-md rounded-2xl mt-[45px] shadow-xl/10 py-6 px-8">
                    <AgentView initial={agents}/>
                </div>
            </div>
        </div>
    );
}