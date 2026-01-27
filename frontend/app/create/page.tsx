'use client'

import { File, Lock, Server, Sparkles, X } from 'lucide-react';
import { motion } from 'motion/react';
import { useState, useRef, useEffect, memo } from 'react';

type FileInputProps = {
    icon: React.ReactNode,
    label: string,
    accept: string,
    file: File | null,
    onFileChange: (file: File | null) => void,
    required?: boolean
}

const FileInput = ({ icon, label, accept, file, onFileChange, required = true }: FileInputProps) => {

    const inputRef = useRef<HTMLInputElement>(null);

    const handleClick = () => {
        inputRef.current?.click();
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0] || null;
        onFileChange(selectedFile);
    };

    const handleRemove = (e: React.MouseEvent) => {
        e.stopPropagation();
        onFileChange(null);
        if (inputRef.current) {
            inputRef.current.value = '';
        }
    };

    return (
        <div onClick={handleClick} className={`relative group cursor-pointer aspect-square rounded-xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center ${file ? 'border-[#2c81e3] bg-[#2c81e3]/5' : 'border-gray-300 hover:border-[#2c81e3] hover:bg-[#2c81e3]/5'}`}>
            <input ref={inputRef} type="file" accept={accept} onChange={handleChange} className="hidden"/>
            {
                file && <div onClick={(e) => { onFileChange(null); e.stopPropagation(); }} className='absolute group hover:bg-red-500/20 text-gray-400 hover:text-red-500 transition-all top-2 right-2 size-6 rounded-full bg-gray-400/10 grid place-items-center'>
                    <X className='' size={17}/>
                </div>
            }
            {icon}
            {
                !file ?
                <>
                    <span className='text-gray-400 group-hover:text-[#2c81e3] transition-all mt-2'>{label}</span>
                    <span className='text-gray-400/50 text-xs group-hover:text-[#2c81e3]/40 transition-all'>{required ? "Required" : "Optional"}</span>
                </>
                    :
                <>
                    <span className='text-gray-400 group-hover:text-[#2c81e3] transition-all mt-2'>{file.name}</span>
                        <span className='text-gray-400/50 text-xs group-hover:text-[#2c81e3]/40 transition-all'>{(file.size / 1000).toFixed(2)} kB</span>
                </> 
            }
        </div>
    );
}

const SteppedSlider = ({ steps, unit, setValue }: { steps: number[], unit: string, setValue: (value: number) => void }) => {

    const [level, setLevel] = useState<number>(0);
    const barRef = useRef<HTMLDivElement | null>(null);
    const constraintsRef = useRef<HTMLDivElement | null>(null);

    const handleDrag = (event: MouseEvent | TouchEvent | PointerEvent, info: { point: { x: number } }) => {
        if (!barRef.current) return;
        
        const barRect = barRef.current.getBoundingClientRect();
        const relativeX = info.point.x - barRect.left;
        const percentage = Math.max(0, Math.min(1, relativeX / barRect.width));
        const newLevel = Math.round(percentage * (steps.length - 1));
        
        setLevel(newLevel);
    };

    const handleStepClick = (index: number) => {
        setLevel(index);
        setValue(steps[index]);
    };

    const sliderPosition = (level / (steps.length - 1)) * 100;

    return (
        <div ref={constraintsRef} className='w-full relative px-2'>
            <div ref={barRef} className='w-full bg-gray-300 rounded-full h-2 relative'>
                <motion.div 
                    className='absolute top-0 bottom-0 left-0 bg-[#2c81e3] rounded-full'
                    animate={{ width: `${sliderPosition}%` }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
                {
                    steps.map((val, key) => (
                        <div key={key} onClick={() => handleStepClick(key)} className='absolute top-1/2 -translate-y-1/2 -translate-x-1/2 cursor-pointer z-10' style={{ left: `${(key / (steps.length - 1)) * 100}%` }}>
                            <motion.div 
                                className={`size-3 rounded-full transition-colors duration-200 ${level >= key ? "bg-[#2c81e3]" : "bg-gray-300"}`}
                                whileHover={{ scale: 1.2 }}
                                whileTap={{ scale: 0.9 }}
                            />
                            <span className='absolute -translate-x-1/2 left-1/2 top-4 text-sm text-gray-400 select-none'>
                                {val}{unit}
                            </span>
                        </div>
                    ))
                }
            </div>
        </div>
    );
}


export default function Create() {

    const [server, setServer] = useState<File | null>(null);
    const [requirements, setRequirements] = useState<File | null>(null);
    const [environment, setEnvironment] = useState<File | null>(null);
    const [title, setTitle] = useState<string | null>(null);
    const [description, setDescription] = useState<string | null>(null);
    const [cpu, setCPU] = useState<number>(25);
    const [memory, setMemory] = useState<number>(128);
    const [storage, setStorage] = useState<number>(1024);
    const [sats, setSats] = useState<number>(0.05);
    const [error, setError] = useState<{ input: "file" | "title", error: string } | null>(null);

    useEffect(() => {

        const cpuCostPerPercent = 0.0005;
        const memoryCostPerMB = 0.0001;
        const storageCostPerMB = 0.00005;

        const totalCost = (cpu * cpuCostPerPercent) + (memory * memoryCostPerMB) + (storage * storageCostPerMB);
        setSats(totalCost);

    }, [cpu, memory, storage])

    return (
        <div className="w-full relative h-screen pt-[100px]">
            <div className="fixed z-10 md:px-20 flex items-center justify-center md:justify-end left-0 shadow-2xl/50 right-0 bottom-0 h-[100px] bg-white">
                <div className="text-lg text-gray-800">Estimated cost per token: <span className="font-bold text-gray-800">{(sats * 0.75).toFixed(2)} - {sats.toFixed(2)} sats</span></div>
            </div>
            <div className="mx-auto w-fit text-[40px] sm:text-[60px] text-white">
                <div>Create an agent.</div>
            </div>
            <div className="max-w-5xl mx-auto px-6 pb-[150px]">
                <div className="bg-white/90 backdrop-blur-md rounded-2xl mt-[45px] shadow-xl/10 py-6 px-8">
                    <div className="flex gap-2 items-center justify-center sm:justify-start mb-6 text-nowrap"> 
                        <h2 className="text-md sm:text-xl text-gray-800">Upload Files</h2>
                        <span className="text-gray-800 text-md self-center">or</span>
                        <div className="hover:scale-105 py-1 px-3 cursor-pointer text-white flex gap-1.5 transition-all duration-300 ease-in-out bg-[#2c81e3a8] rounded-full items-center justify-center">
                            <Sparkles size={16} strokeWidth={2}/>
                            <div className=''>Create with AI</div>
                        </div>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
                        <FileInput
                            icon={<Server className='text-gray-400 group-hover:text-[#2c81e3] transition-all' size={30}/>}
                            label="Server"
                            accept=".py,.txt"
                            file={server}
                            onFileChange={(file: File | null) => setServer(file)}
                        />
                        <FileInput
                            icon={<File className='text-gray-400 group-hover:text-[#2c81e3] transition-all' size={30}/>}
                            label="Requirements"
                            accept=".txt"
                            file={requirements}
                            onFileChange={(file: File | null) => setRequirements(file)}
                            required={false}
                        />
                        <FileInput
                            icon={<Lock className='text-gray-400 group-hover:text-[#2c81e3] transition-all' size={30}/>}
                            label="Environment"
                            accept=".env"
                            file={environment}
                            onFileChange={(file: File | null) => setEnvironment(file)}
                            required={false}
                        />
                    </div>
                    <div className="text-nowrap mb-6">
                        <h2 className="text-md sm:text-xl text-gray-800">Title</h2>
                        <span className='text-gray-800/50 text-md block mb-2'>Give your agent a short, memorable name.</span>
                        <div className='relative'>
                            <input 
                                type="text" 
                                placeholder="Title..."
                                className="w-full px-4 py-2.5 rounded-xl border-2 border-gray-300 focus:border-[#2c81e3] focus:outline-none transition-colors text-gray-800 placeholder:text-gray-400"
                                onChange={(e) => setTitle(prev => e.target.value.length > 30 ? prev : e.target.value)}
                                maxLength={30}
                            />
                            <div className='absolute bottom-[105%] right-1'>
                                <span className='text-gray-800/50'>{title?.length ?? 0}/30</span>
                            </div>
                        </div>
                    </div>
                    <div className="mb-6 text-nowrap">
                        <h2 className="text-md sm:text-xl text-gray-800">Description</h2>
                        <span className='text-gray-800/50 text-md block mb-2'>Let others know what your agent can do.</span>
                        <div className='relative w-full pl-4 pr-2 py-2.5 rounded-xl border-2 border-gray-300 focus:border-[#2c81e3] '>
                            <textarea 
                                placeholder="Description..."
                                rows={4}
                                className="w-full scrollbar focus:outline-none transition-colors text-gray-800 placeholder:text-gray-400 resize-none"
                                maxLength={500}
                                onChange={(e) => setDescription(prev => e.target.value.length > 500 ? prev : e.target.value)}
                            />
                            <div className='absolute bottom-[105%] right-1'>
                                <span className='text-gray-800/50'>{description?.length ?? 0}/500</span>
                            </div>
                        </div>
                    </div>
                    <div className="mb-12 text-nowrap">
                        <h2 className="text-md sm:text-xl text-gray-800">CPU</h2>
                        <span className='text-gray-800/50 text-md block mb-3'>Choose how much processing power your agent can use.</span>
                        <SteppedSlider steps={[25, 50, 75, 100]} unit="%" setValue={setCPU}/>
                    </div>  
                    <div className="mb-12 text-nowrap">
                        <h2 className="text-md sm:text-xl text-gray-800">Memory</h2>
                        <span className='text-gray-800/50 text-md block mb-3'>The amount of RAM your agent has access to.</span>
                        <SteppedSlider steps={[128, 352, 576, 800, 1024]} unit="MB" setValue={setMemory}/>
                    </div>  
                    <div className="mb-12 text-nowrap">
                        <h2 className="text-md sm:text-xl text-gray-800">Storage</h2>
                        <span className='text-gray-800/50 text-md block mb-3'>Set the disk space your agent can use for data and files.</span>
                        <SteppedSlider steps={[1024, 2048, 3072, 4096, 5120]} unit="MB" setValue={setStorage}/>
                    </div>  
                    <div className='flex gap-5 justify-center items-center w-full'>
                        <div className="hover:scale-110 active:scale-90 py-1 px-3 cursor-pointer text-white flex gap-1.5 transition-all duration-500 ease-in-out bg-[#2c81e3a8] rounded-full items-center justify-center">
                            <div className=''>Continue</div>
                        </div>
                        <div className="hover:scale-110 active:scale-90 py-1 px-3 cursor-pointer text-gray-500 border-gray-500 border-2 flex gap-1.5 transition-all duration-500 ease-in-out rounded-full items-center justify-center">
                            <div className=''>Preview</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    ); 
}