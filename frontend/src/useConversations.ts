import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import {
  api,
  consume,
  isAbort,
  onSessionInvalidated,
  ownsSession,
  request,
  sessionStamp,
} from "./api";
import type {
  Chat,
  Conversation,
  Message,
  Model,
  Page,
  User,
} from "./contracts";

/** One owner for navigation, requests and streams; screens only render state. */
export function useConversations(
  user: User | null,
  notify: (message: string) => void,
) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [filter, updateFilter] = useState("");
  const filterRef = useRef("");
  const [listBusy, setListBusy] = useState(false);
  const [historyBusy, setHistoryBusy] = useState(false);
  const historyVersion = useRef(0);
  const history = useRef<AbortController | null>(null);
  const [selected, setSelected] = useState("");
  const [title, setTitle] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [messagesCursor, setMessagesCursor] = useState<string | null>(null);
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [models, setModels] = useState<Model[]>([]);
  const [model, setModel] = useState("default");
  const identity = useRef(user?.id);
  identity.current = user?.id;
  const generation = useRef(0);
  const view = useRef(0);
  const listVersion = useRef(0);
  const selectedRef = useRef("");
  const stream = useRef<AbortController | null>(null);
  const load = useRef<AbortController | null>(null);
  const listing = useRef<AbortController | null>(null);
  const run = useRef("");
  const stamp = sessionStamp();
  const owner = () => ({
    id: identity.current,
    generation: generation.current,
    stamp: sessionStamp(),
  });
  type Owner = ReturnType<typeof owner>;
  const owns = (value: Owner) =>
    value.id !== undefined &&
    value.id === identity.current &&
    value.generation === generation.current &&
    ownsSession(value.stamp);
  const error = (value: unknown) => {
    if (!isAbort(value))
      notify(value instanceof Error ? value.message : "Something went wrong.");
  };
  function invalidate() {
    generation.current++;
    view.current++;
    listVersion.current++;
    historyVersion.current++;
    stream.current?.abort();
    load.current?.abort();
    listing.current?.abort();
    history.current?.abort();
    stream.current = null;
    run.current = "";
  }
  function clear() {
    invalidate();
    selectedRef.current = "";
    setChats([]);
    setNextCursor(null);
    setMessages([]);
    setMessagesCursor(null);
    setSelected("");
    setTitle("");
    setPrompt("");
    setBusy(false);
    setModels([]);
    filterRef.current = "";
    updateFilter("");
    setListBusy(false);
    setHistoryBusy(false);
  }
  function setFilter(value: string) {
    filterRef.current = value;
    listVersion.current++;
    listing.current?.abort();
    setNextCursor(null);
    setChats([]);
    updateFilter(value);
  }
  async function listChats(expected = owner(), cursor?: string) {
    if (!owns(expected)) return;
    listing.current?.abort();
    const controller = new AbortController();
    listing.current = controller;
    const version = ++listVersion.current;
    setListBusy(true);
    const query = new URLSearchParams({
      page: "true",
      limit: "50",
      q: filterRef.current,
    });
    if (cursor) query.set("cursor", cursor);
    try {
      const page = await api<Page<Chat>>(
        "/conversations?" + query,
        "GET",
        undefined,
        controller.signal,
      );
      if (!owns(expected) || version !== listVersion.current) return;
      setChats((current) =>
        cursor
          ? [
              ...current,
              ...page.items.filter(
                (item) => !current.some((old) => old.id === item.id),
              ),
            ]
          : page.items,
      );
      setNextCursor(page.next_cursor);
    } catch (e) {
      if (owns(expected) && version === listVersion.current) error(e);
    } finally {
      if (owns(expected) && version === listVersion.current) setListBusy(false);
    }
  }
  async function loadConversation(
    id: string,
    expected: Owner,
    version: number,
  ) {
    load.current?.abort();
    const controller = new AbortController();
    load.current = controller;
    try {
      const conversation = await api<Conversation>(
        "/conversations/" + id,
        "GET",
        undefined,
        controller.signal,
      );
      if (
        !owns(expected) ||
        version !== view.current ||
        selectedRef.current !== id
      )
        return;
      setMessages(conversation.messages);
      setMessagesCursor(conversation.messages_cursor);
      setTitle(conversation.title);
    } catch (e) {
      if (owns(expected) && version === view.current) error(e);
    }
  }
  async function openChat(id: string) {
    const expected = owner();
    const version = ++view.current;
    historyVersion.current++;
    history.current?.abort();
    setHistoryBusy(false);
    selectedRef.current = id;
    setSelected(id);
    setMessages([]);
    setMessagesCursor(null);
    setTitle(
      chats.find((chat) => chat.id === id)?.title ?? "Loading conversation…",
    );
    await loadConversation(id, expected, version);
  }
  async function newChat() {
    const expected = owner();
    const version = ++view.current;
    load.current?.abort();
    const chat = await api<Chat>("/conversations", "POST");
    if (!owns(expected) || version !== view.current)
      throw new DOMException("Conversation changed", "AbortError");
    selectedRef.current = chat.id;
    setSelected(chat.id);
    setTitle(chat.title);
    setMessages([]);
    setMessagesCursor(null);
    await listChats(expected);
    return chat.id;
  }
  async function send(e?: FormEvent, retryText?: string) {
    e?.preventDefault();
    const content = retryText ?? prompt;
    if (!content.trim() || busy || stream.current) return;
    const expected = owner();
    if (!owns(expected)) return;
    const controller = new AbortController();
    stream.current = controller;
    const ownsStream = () => owns(expected) && stream.current === controller;
    setBusy(true);
    notify("");
    setPrompt("");
    run.current = "";
    let cid = selectedRef.current;
    let version = view.current;
    try {
      if (!cid) {
        cid = await newChat();
        version = view.current;
      }
      if (!ownsStream()) return;
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "user", content },
        { id: "live", role: "assistant", content: "" },
      ]);
      const response = await request("/conversations/" + cid + "/stream", {
        method: "POST",
        body: JSON.stringify({
          content,
          request_key: crypto.randomUUID(),
          model,
        }),
        signal: controller.signal,
      });
      await consume(response, (event) => {
        if (
          !ownsStream() ||
          view.current !== version ||
          selectedRef.current !== cid
        )
          return;
        if (event.kind === "started") run.current = event.run_id;
        if (event.kind === "delta")
          setMessages((current) =>
            current.map((item) =>
              item.id === "live"
                ? { ...item, content: item.content + event.text }
                : item,
            ),
          );
        if (event.kind === "error") notify(event.message);
        if (event.kind === "completed" && event.status === "incomplete")
          notify(
            "The reply stopped before completion. Partial text was saved.",
          );
        if (event.kind === "completed" && event.status === "refused")
          notify("The provider declined this reply.");
      });
    } catch (e) {
      if (ownsStream() && !isAbort(e)) {
        error(e);
        if (!run.current) setPrompt(content);
      }
    } finally {
      controller.abort();
      if (ownsStream()) {
        stream.current = null;
        run.current = "";
        setBusy(false);
        if (cid && selectedRef.current === cid && version === view.current)
          await loadConversation(cid, expected, version);
        if (owns(expected)) await listChats(expected);
      }
    }
  }
  async function stop() {
    const expected = owner();
    const controller = stream.current;
    const id = run.current;
    try {
      if (id) await api<void>("/generations/" + id + "/cancel", "POST");
    } catch (e) {
      if (owns(expected)) error(e);
    } finally {
      controller?.abort();
    }
  }
  async function rename(value: string) {
    const expected = owner();
    const id = selectedRef.current;
    await api<Chat>("/conversations/" + id, "PATCH", { title: value });
    if (owns(expected) && selectedRef.current === id) setTitle(value);
    if (owns(expected)) await listChats(expected);
  }
  async function remove() {
    const expected = owner();
    const id = selectedRef.current;
    await api<void>("/conversations/" + id, "DELETE");
    if (!owns(expected) || selectedRef.current !== id) return;
    view.current++;
    selectedRef.current = "";
    setSelected("");
    setTitle("");
    setMessages([]);
    setMessagesCursor(null);
    await listChats(expected);
  }
  async function olderMessages() {
    const expected = owner();
    const id = selectedRef.current;
    const version = view.current;
    if (!messagesCursor) return;
    history.current?.abort();
    const controller = new AbortController();
    history.current = controller;
    const pageVersion = ++historyVersion.current;
    setHistoryBusy(true);
    const query = new URLSearchParams({ cursor: messagesCursor, limit: "50" });
    try {
      const page = await api<Page<Message>>(
        "/conversations/" + id + "/messages?" + query,
        "GET",
        undefined,
        controller.signal,
      );
      if (
        !owns(expected) ||
        selectedRef.current !== id ||
        version !== view.current ||
        pageVersion !== historyVersion.current
      )
        return;
      setMessages((current) => [
        ...page.items.filter(
          (item) => !current.some((old) => old.id === item.id),
        ),
        ...current,
      ]);
      setMessagesCursor(page.next_cursor);
    } catch (value) {
      if (
        owns(expected) &&
        version === view.current &&
        pageVersion === historyVersion.current
      )
        error(value);
    } finally {
      if (
        owns(expected) &&
        version === view.current &&
        pageVersion === historyVersion.current
      )
        setHistoryBusy(false);
    }
  }
  useEffect(() => {
    clear();
    const unsubscribe = onSessionInvalidated(clear);
    const expected = owner();
    if (user) {
      listChats(expected);
      api<Model[]>("/models")
        .then((value) => {
          if (owns(expected)) setModels(value);
        })
        .catch((e) => {
          if (owns(expected)) error(e);
        });
    }
    return () => {
      unsubscribe();
      invalidate();
    };
  }, [user?.id, stamp]);
  useEffect(() => {
    if (!user) return;
    const expected = owner();
    const timer = setTimeout(() => listChats(expected), 200);
    return () => clearTimeout(timer);
  }, [filter, user?.id, stamp]);
  return {
    chats,
    selected,
    title,
    messages,
    messagesCursor,
    historyBusy,
    listBusy,
    prompt,
    setPrompt,
    busy,
    models,
    model,
    setModel,
    filter,
    setFilter,
    nextCursor,
    listChats,
    openChat,
    newChat,
    send,
    stop,
    rename,
    remove,
    olderMessages,
    moreChats: () => listChats(owner(), nextCursor ?? undefined),
  };
}
