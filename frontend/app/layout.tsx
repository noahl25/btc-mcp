import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import "./globals.css";

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

export default function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html lang="en">
			<body
				className={`${dmSans.variable} antialiased`}
			>
				{children}
			</body>
		</html>
	);
}
