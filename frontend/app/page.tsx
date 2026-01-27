import HeroButton from "@/components/HeroButton";
import Navbar from "@/components/Navbar";
import Image from "next/image";

export default function Home() {
    return (
        <div className="overflow-hidden h-screen relative">

            <Image 
                src="/assets/images/city.png" 
                alt="City background" 
                width={2560}
                height={1440}
                className="absolute bottom-0 left-0 w-[200vw] -z-2 translate-y-[20%] sm:translate-y-[35%]"
                loading="eager"
            />
            <div className="absolute bottom-0 left-0 w-screen -z-1 h-[520px]" style={{
                background: "linear-gradient(to bottom, transparent 50%, white 95%)",
            }}/>
            <div className="mt-[100px] w-full text-center md:text-left md:mx-20 mx-auto px-10 sm:px-0 text-[40px] sm:text-[60px] text-white">
                <div className="leading-12 sm:leading-15">Deploy your agents.</div>
                <div className="leading-12 sm:leading-15">Earn with Bitcoin.</div>
                <p className="text-[15px] sm:text-[20px] text-center md:text-left opacity-70 leading-4 sm:leading-6 mt-4">Trustless, decentralized access to MCP servers. <br/> Create your own custom agents and seamlessly interact with others. </p>
                <HeroButton className="mt-5"/>
            </div>
        </div>
    );
}
