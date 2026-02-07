"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { motion } from "motion/react";

type PaymentInfo = {
    earnings: number,
    staked: number,
    total_staked: number
}

export default function Payments() {
    const [data, setData] = useState<PaymentInfo | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [invoice, setInvoice] = useState("");
    const [withdrawing, setWithdrawing] = useState(false);
    const [withdrawMessage, setWithdrawMessage] = useState<string | null>(null);

    useEffect(() => {
        fetchPaymentInfo();
    }, [])

    const fetchPaymentInfo = async () => {
        try {
            setLoading(true);
            const response = await axios.post(
                "http://localhost:8000/api/payments/me",
                {},
                { withCredentials: true }
            );
            setData(response.data);
            setError(null);
        } catch {
            setError("Stake or create an agent before accessing payments.");
        } finally {
            setLoading(false);
        }
    }

    const handleWithdraw = async () => {
        if (!invoice.trim()) {
            setWithdrawMessage("Please enter a Lightning invoice.");
            return;
        }

        try {
            setWithdrawing(true);
            setWithdrawMessage(null);
            const response = await axios.post(
                "http://localhost:8000/api/payments/withdraw",
                { invoice: invoice },
                { withCredentials: true }
            );
            if (response.data.status === "success") {
                setWithdrawMessage("Withdrawal successful!");
                setInvoice("");
                fetchPaymentInfo();
            } else {
                setWithdrawMessage(response.data.message || "Withdrawal failed.");
            }
        } catch (err: unknown) {
            const error = err as { response?: { data?: { message?: string } } };
            setWithdrawMessage(error.response?.data?.message || "Withdrawal failed.");
        } finally {
            setWithdrawing(false);
        }
    }

    const formatCredits = (credits: number) => {
        return credits.toLocaleString();
    }

    const creditsToUSD = (credits: number) => {
        const cents = credits / 20;
        return (cents / 100).toFixed(2);
    }

    const dotVariants = {
        loading: (i: number) => ({
            y: [0, -12, 0],
            backgroundColor: "#2c81e3",
            transition: {
                y: {
                    repeat: Infinity,
                    duration: 1,
                    ease: "easeInOut" as const,
                    delay: i * 0.15,
                },
            },
        })
    }

    return (
        <div className="w-full relative pt-[100px]">
            <div className="mx-auto w-fit text-[40px] sm:text-[60px] text-white">
                <div>Payments</div>
            </div>
            <div className="max-w-3xl mx-auto px-6 pb-[150px]">
                <div className="bg-white/90 backdrop-blur-md rounded-2xl mt-[45px] shadow-xl/10 py-8 px-8">
                    {loading ? (
                        <div className={`flex gap-2 items-center justify-center`}>
                            {[0, 1, 2].map((i) => (
                                <motion.div
                                    key={i}
                                    custom={i}
                                    variants={dotVariants}
                                    animate="loading"
                                    className="size-3 rounded-full bg-[#2c81e3]"
                                />
                            ))}
                        </div>
                    ) : error ? (
                        <div className="text-center py-8">{error}</div>
                    ) : data ? (
                        <div className="space-y-8">
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div className="border relative border-gray-200 rounded-xl shadow-md hover:shadow-xl border-2 border-gray-400/40 transition-shadow duration-500 ease-in-out cursor-pointer bg-white">
                                    <div className="px-6 py-5">
                                        <div className="text-sm text-gray-800 font-medium mb-1">Earnings (Credits)</div>
                                        <div className="text-3xl font-bold text-[#2c81e3] truncate">{formatCredits(data.earnings)}</div>
                                        <div className="text-sm text-gray-600 mt-1">≈ ${creditsToUSD(data.earnings)} USD</div>
                                    </div>
                                </div>
                                <div className="border relative border-gray-200 rounded-xl shadow-md hover:shadow-xl border-2 border-gray-400/40 transition-shadow duration-500 ease-in-out cursor-pointer bg-white">
                                    <div className="px-6 py-5">
                                        <div className="text-sm text-gray-800 font-medium mb-1">Claimable Stakes</div>
                                                <div className="text-3xl font-bold text-[#2c81e3] truncate">{formatCredits(data.staked)}</div>
                                        <div className="text-sm text-gray-600 mt-1">≈ ${creditsToUSD(data.staked)} USD</div>
                                    </div>
                                </div>

                                <div className="border relative border-gray-200 rounded-xl shadow-md hover:shadow-xl border-2 border-gray-400/40 transition-shadow duration-500 ease-in-out cursor-pointer bg-white">
                                    <div className="px-6 py-5">
                                        <div className="text-sm text-gray-800 font-medium mb-1">Total Staked</div>
                                        <div className="text-3xl font-bold text-[#2c81e3] truncate">{formatCredits(data.total_staked)}</div>
                                        <div className="text-sm text-gray-600 mt-1">≈ ${creditsToUSD(data.total_staked)} USD</div>
                                    </div>
                                </div>
                            </div>

                            <div className="border relative border-gray-200 rounded-xl shadow-md hover:shadow-xl border-2 border-gray-400/40 transition-shadow duration-500 ease-in-out cursor-pointer bg-white mt-8">
                                <div className="px-6 py-5">
                                    <div className="text-sm text-gray-800 font-medium mb-1">Total Available to Withdraw</div>
                                    <div className="text-4xl font-bold text-[#2c81e3]">
                                        {formatCredits(data.earnings + data.staked)} credits
                                    </div>
                                    <div className="text-lg text-gray-600 mt-1">
                                        ≈ ${creditsToUSD(data.earnings + data.staked)} USD
                                    </div>
                                </div>
                            </div>
                            <div className="border-t pt-6">
                                <h3 className="text-lg font-semibold text-gray-800 mb-2">Withdraw</h3>
                                <p className="text-sm text-gray-600 mb-4">
                                    Enter a Lightning invoice to withdraw your available balance. Stakes become claimable after 7 days.
                                </p>
                                <div className="flex flex-col sm:flex-row gap-3">
                                    <input
                                        type="text"
                                        placeholder="Paste Lightning invoice here..."
                                        value={invoice}
                                        onChange={(e) => setInvoice(e.target.value)}
                                        className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    />
                                    <button
                                        onClick={handleWithdraw}
                                        disabled={withdrawing || (data.earnings + data.staked) <= 0}
                                        className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                                    >
                                        {withdrawing ? "Processing..." : "Withdraw"}
                                    </button>
                                </div>
                                {withdrawMessage && (
                                    <div className={`mt-3 text-sm ${withdrawMessage.includes("successful") ? "text-green-600" : "text-red-600"}`}>
                                        {withdrawMessage}
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : null}
                </div>
            </div>
        </div>
    );
}