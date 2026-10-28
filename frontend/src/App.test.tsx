import {fireEvent,render,screen,waitFor} from "@testing-library/react";
import {afterEach,expect,test,vi} from "vitest";
import App from "./App";

afterEach(()=>vi.restoreAllMocks());

test("logs in and renders the Arabic task dashboard",async()=>{
  vi.spyOn(globalThis,"fetch")
    .mockResolvedValueOnce(new Response(JSON.stringify({access_token:"test-token"}),{status:200,headers:{"Content-Type":"application/json"}}))
    .mockResolvedValueOnce(new Response(JSON.stringify([{id:1,title:"مهمة تجريبية",description:"وصف واضح",status:"todo",priority:"high",created_at:"2026-01-01T00:00:00Z"}]),{status:200,headers:{"Content-Type":"application/json"}}));
  render(<App/>);
  fireEvent.click(screen.getByRole("button",{name:"دخول آمن"}));
  await waitFor(()=>expect(screen.getByRole("heading",{name:"لوحة متابعة المهام"})).toBeInTheDocument());
  expect(screen.getByText("مهمة تجريبية")).toBeInTheDocument();
});

