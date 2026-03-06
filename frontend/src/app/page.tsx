import { ContextDrawer } from "@/components/layout/ContextDrawer";
import { ChatStream } from "@/components/chat/ChatStream";

export default function Home() {
  return (
    <>
      {/* Collapsible Context Drawer (30%) */}
      <ContextDrawer />

      {/* Primary Chat Stream (70%) */}
      <section className="flex-1 flex flex-col bg-slate-50 relative border-l border-border h-full">
        <ChatStream />
      </section>
    </>
  );
}
