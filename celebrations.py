"""Gold fountain + 5-second notice, rendered directly in Streamlit (no JS/CDN)."""
import html
import random
import uuid
import streamlit as st


def new_milestones(current, previous, seen):
    """Baseline the first successful snapshot; only celebrate subsequent new marks."""
    tokens = {(str(k), str(v)) for k, v in current.items()}
    if previous is None:
        seen.update(tokens)
        return []
    fresh = sorted(k for k, v in tokens if (k, v) not in seen and previous.get(k) != current.get(k))
    seen.update(tokens)
    return fresh


def render_celebration(kind="welcome", message=""):
    config = {"welcome": (2.8, 1.0, 110), "zone": (3.0, 1.1, 150), "show": (5.0, 2.8, 240)}
    duration, launch_window, count = config[kind]
    uid = "gold-" + uuid.uuid4().hex
    rng = random.Random(21)
    pieces = []
    for i in range(count):
        side = "left" if i % 2 == 0 else "right"
        sign = 1 if side == "left" else -1
        dx = sign * rng.uniform(8, 43)
        peak = rng.uniform(28, 68)
        delay = rng.uniform(0, launch_window)
        flight = rng.uniform(1.15, min(1.8, duration - launch_window))
        color = rng.choice(["#FFE7A0", "#D9B85E", "#F6CF64", "#FFF4CF", "#BE8F32"])
        pieces.append(f'<i class="gold-piece {side} p{i % 3}" style="--dx:{dx:.2f}vw;--peak:-{peak:.2f}vh;'
                      f'--spin:{rng.randint(180,720)}deg;--flight:{flight:.2f}s;--delay:{delay:.2f}s;'
                      f'--gold:{color}"></i>')
    notice = (f'<div class="gold-notice" role="status" aria-live="polite">'
              f'<strong>✦ SOLD OUT ✦</strong><span>{html.escape(message)}</span></div>') if message else ""
    markup = '''
<style>
#UID {position:fixed;inset:0;z-index:999990;pointer-events:none;overflow:hidden;
    animation:gold-close DURATIONs step-end forwards!important;}
#UID .gold-piece {position:absolute;bottom:-12px;width:4px;height:11px;background:var(--gold);
    opacity:0;box-shadow:0 0 4px rgba(255,211,94,.3);transform-origin:center;
    animation:gold-flight var(--flight) cubic-bezier(.12,.35,.52,1) var(--delay) both!important;}
#UID .left {left:2%;} #UID .right {right:2%;}
#UID .p1 {width:3px;height:7px;} #UID .p2 {width:3px;height:3px;border-radius:50%;}
@keyframes gold-flight {
  0% {opacity:0;transform:translate(0,0) rotate(0deg);}
  5% {opacity:1;}
  45% {opacity:1;transform:translate(calc(var(--dx)*.65),var(--peak)) rotate(var(--spin));}
  100% {opacity:0;transform:translate(var(--dx),15vh) rotate(calc(var(--spin)*2));}
}
@keyframes gold-close {0% {visibility:visible;} 100% {visibility:hidden;}}
#UID-notice {position:fixed;top:78px;right:24px;z-index:999991;pointer-events:none;
    width:min(420px,calc(100vw - 32px));
    animation:gold-close 5s step-end forwards!important;}
#UID-notice .gold-notice {padding:18px 22px;background:#300807;border:1px solid #D9B85E;
    border-radius:12px;box-shadow:0 8px 32px #10000066;color:#FFF0CB;
    font:16px/1.5 system-ui,sans-serif;overflow-wrap:anywhere;}
#UID-notice strong {display:block;color:#F6CF64;font-size:14px;letter-spacing:.12em;margin-bottom:5px;}
#UID-notice span {display:block;}
@media(max-width:767px){
    #UID .p1,#UID .p2 {display:none;}
    #UID-notice {right:16px;top:72px;}
}
@media(prefers-reduced-motion:reduce){
    #UID {display:none!important;}
    #UID-notice {animation:gold-close 5s step-end forwards!important;}
}
</style>
<div id="UID" aria-hidden="true">PIECES</div>
<div id="UID-notice">NOTICE</div>
'''
    markup = markup.replace("DURATION", str(duration)).replace("PIECES", "".join(pieces)).replace("NOTICE", notice).replace("UID", uid)
    st.markdown(markup, unsafe_allow_html=True)
