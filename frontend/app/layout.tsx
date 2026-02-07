import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import { AuthProvider } from "@/components/AuthContext";
import { cookies } from "next/headers";

const dmSans = DM_Sans({
	variable: "--font-default",
	subsets: ["latin"],
});


export const metadata: Metadata = {
	title: "btc-mcp",
	icons: {
		icon: [
			{
				media: '(prefers-color-scheme: light)',
				url: '/assets/images/icon-light.png',
				href: '/assets/images/icon-light.png',
			},
			{
				media: '(prefers-color-scheme: dark)',
				url: '/assets/images/icon-dark.png',
				href: '/assets/images/icon-dark.png',
			},
		],
	},
};

export default async function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	const cookieStore = await cookies();
	const cookieHeader = cookieStore.getAll().map(c => `${c.name}=${c.value}`).join("; ");
	const res = await fetch(`http://localhost:8000/creator/session`, {
		headers: {
			cookie: cookieHeader,
		},
		cache: "no-store",
	});

	let authenticated = false;
	if (res.ok) {
		const result = await res.json();
		authenticated = Boolean(result?.authenticated);
	}

	return (
		<html lang="en">
			<body className={`${dmSans.variable} antialiased overflow-x-hidden`}>
				<AuthProvider initial={authenticated}>
					<Navbar />
					<div
						className="absolute inset-0 -z-1"
						style={{
							background:
								"radial-gradient(120% 70% at 50% 0%, #4a8fdda8 30%, #00000000)",
						}}
					/>
					{children}
				</AuthProvider>
			</body>
		</html>
	);
}
