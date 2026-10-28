import {FormEvent, useEffect, useMemo, useState} from "react";

type Status="todo"|"doing"|"done";
type Priority="low"|"medium"|"high";
type Task={id:number;title:string;description:string;status:Status;priority:Priority;created_at:string};

const API=import.meta.env.VITE_API_URL??"http://localhost:8000";
const statusLabel:Record<Status,string>={todo:"بانتظار البدء",doing:"قيد التنفيذ",done:"مكتملة"};
const priorityLabel:Record<Priority,string>={low:"منخفضة",medium:"متوسطة",high:"عالية"};

async function request<T>(path:string,options:RequestInit={},token?:string):Promise<T>{
  const response=await fetch(`${API}${path}`,{
    ...options,
    headers:{"Content-Type":"application/json",...(token?{Authorization:`Bearer ${token}`}:{})},
  });
  if(!response.ok)throw new Error(response.status===401?"تعذر تسجيل الدخول":"تعذر إتمام الطلب");
  return response.status===204?undefined as T:response.json();
}

function Login({onLogin}:{onLogin:(token:string)=>void}){
  const [username,setUsername]=useState("demo_admin");
  const [password,setPassword]=useState("Demo123!");
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(false);
  async function submit(event:FormEvent){
    event.preventDefault();setLoading(true);setError("");
    try{const result=await request<{access_token:string}>("/auth/login",{method:"POST",body:JSON.stringify({username,password})});onLogin(result.access_token)}
    catch(reason){setError(reason instanceof Error?reason.message:"تعذر تسجيل الدخول")}
    finally{setLoading(false)}
  }
  return <main className="login-shell"><section className="login-card">
    <div className="brand-mark">✓</div><p className="eyebrow">نموذج هندسي عام</p>
    <h1>Secure TaskFlow</h1><p className="muted">لوحة مهام عربية مبنية بـ React وFastAPI وPostgreSQL.</p>
    <form onSubmit={submit}><label>اسم المستخدم<input value={username} onChange={e=>setUsername(e.target.value)}/></label><label>كلمة المرور<input type="password" value={password} onChange={e=>setPassword(e.target.value)}/></label>
      {error&&<p role="alert" className="error">{error}</p>}<button disabled={loading}>{loading?"جارٍ الدخول...":"دخول آمن"}</button></form>
    <p className="demo-note">حساب العرض معبأ مسبقًا · بيانات اصطناعية فقط</p>
  </section></main>;
}

export default function App(){
  const [token,setToken]=useState("");const [tasks,setTasks]=useState<Task[]>([]);const [error,setError]=useState("");const [loading,setLoading]=useState(false);
  async function load(currentToken=token){setLoading(true);try{setTasks(await request<Task[]>("/tasks",{},currentToken));setError("")}catch(reason){setError(reason instanceof Error?reason.message:"تعذر التحميل")}finally{setLoading(false)}}
  useEffect(()=>{if(token)void load(token)},[token]);
  const totals=useMemo(()=>({all:tasks.length,doing:tasks.filter(t=>t.status==="doing").length,done:tasks.filter(t=>t.status==="done").length}),[tasks]);
  async function advance(task:Task){const next:Status=task.status==="todo"?"doing":"done";const updated=await request<Task>(`/tasks/${task.id}`,{method:"PATCH",body:JSON.stringify({status:next})},token);setTasks(current=>current.map(item=>item.id===updated.id?updated:item))}
  if(!token)return <Login onLogin={setToken}/>;
  return <div className="app-shell"><aside><div className="sidebar-brand"><span>✓</span><b>TaskFlow</b></div><nav><a className="active">لوحة العمل</a><a>التقارير</a><a>إعدادات الفريق</a></nav><div className="secure-note"><b>اتصال آمن</b><small>صلاحيات وتدقيق مركزي</small></div></aside>
    <main className="dashboard"><header><div><p className="eyebrow">مساحة الفريق</p><h1>لوحة متابعة المهام</h1><p className="muted">نظرة واضحة على العمل والأولويات وحالة الإنجاز.</p></div><button className="outline" onClick={()=>setToken("")}>تسجيل الخروج</button></header>
      <section className="stats"><article><span>جميع المهام</span><strong>{totals.all}</strong></article><article><span>قيد التنفيذ</span><strong>{totals.doing}</strong></article><article><span>مكتملة</span><strong>{totals.done}</strong></article></section>
      <section className="panel"><div className="panel-head"><div><h2>سير العمل</h2><p>بيانات عرض اصطناعية قابلة للتحديث عبر API.</p></div><button onClick={()=>void load()} disabled={loading}>{loading?"جارٍ التحديث...":"تحديث"}</button></div>
        {error&&<p role="alert" className="error">{error}</p>}<div className="task-grid">{tasks.map(task=><article className="task-card" key={task.id}><div className="task-top"><span className={`status ${task.status}`}>{statusLabel[task.status]}</span><span className={`priority ${task.priority}`}>{priorityLabel[task.priority]}</span></div><h3>{task.title}</h3><p>{task.description}</p><footer><small>مهمة #{task.id}</small>{task.status!=="done"&&<button onClick={()=>void advance(task)}>{task.status==="todo"?"بدء التنفيذ":"إكمال"}</button>}</footer></article>)}</div>
      </section><footer className="page-footer">React · TypeScript · FastAPI · PostgreSQL · CI</footer>
    </main></div>;
}

