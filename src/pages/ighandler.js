(function() {
    const $ = (id) => document.getElementById(id);
    const els = {
        pSec: $('profileSection'), rCon: $('resultsContainer'), eCon: $('errorContainer'),
        sBtn: $('searchBtn'), uIn: $('usernameInput'), cBtn: $('compareBtn'), xBtn: $('exportBtn'),
        nList: $('nonFollowersList'), nTitle: $('nonFollowerTitle'), pAv: $('profileAvatar'),
        pUn: $('profileUsername'), pBio: $('profileBio'), pC: $('postCount'),
        fC: $('followersCount'), fwC: $('followingCount')
    };

    let state = { u: null, p: null, fws: null, fwg: null, busy: false };
    const wl = new Set(['instagram', 'meta', 'creators']); 

    const log = (m, t = 'error') => {
        els.eCon.innerHTML = `<div class="msg-${t}" style="padding:12px; border-radius:8px; margin-bottom:10px; background:${t==='error'?'#450a0a':'#064e3b'}; border:1px solid ${t==='error'?'#ef4444':'#10b981'}">${m}</div>`;
        if(t === 'error') setTimeout(() => els.eCon.innerHTML = '', 6000);
    };

    const esc = (s) => (s||'').toString().replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":"&#39;"}[m]));
    
    const getVal = (obj, paths) => {
        for (let p of paths) {
            let v = p.split('.').reduce((a, c) => a?.[c], obj);
            if (v !== undefined && v !== null) return v;
        }
        return 0;
    };

    const fetchP = async () => {
        const raw = els.uIn.value.trim();
        const u = raw.replace(/^@/, '').match(/(?:instagr\.am|instagram\.com)\/([a-zA-Z0-9_.]+)/)?.[1] || raw.split('/')[0].split('?')[0];
        
        if (!u || state.busy) return;
        const h = window.IGHandler || IGHandler;
        if (!h) return log("System Critical: IGHandler Bridge Offline");

        state.busy = true;
        els.sBtn.innerHTML = `<i class="fas fa-circle-notch fa-spin"></i>`;
        
        try {
            const d = await (h.getUserInfo || h.getProfile)(u);
            
            if (d.is_private) {
                log(`Security Alert: @${u} is a Private Account. Business insights unavailable.`, 'error');
                throw new Error("PRIVATE_ACC");
            }

            state.p = {
                u: d.username || u,
                pic: getVal(d, ['profile_pic_url_hd', 'profile_pic_url', 'avatar']),
                bio: d.biography || d.bio || '',
                pc: getVal(d, ['edge_owner_to_timeline_media.count', 'media_count', 'posts']),
                fc: getVal(d, ['edge_followed_by.count', 'follower_count', 'followers']),
                fwc: getVal(d, ['edge_follow.count', 'following_count', 'following']),
                ver: d.is_verified || false,
                biz: d.is_business_account || d.is_professional_account || false
            };
            
            state.u = state.p.u;
            state.fws = state.fwg = null;

            els.pAv.src = state.p.pic;
            els.pUn.innerHTML = `${state.u} ${state.p.ver ? '✔️' : ''}`;
            els.pBio.textContent = state.p.bio;
            els.pC.textContent = Number(state.p.pc).toLocaleString();
            els.fC.textContent = Number(state.p.fc).toLocaleString();
            els.fwC.textContent = Number(state.p.fwc).toLocaleString();

            els.pSec.style.display = 'block';
            els.rCon.style.display = 'none';
            els.cBtn.disabled = false;
        } catch (e) {
            els.pSec.style.display = 'none';
            if(e.message !== "PRIVATE_ACC") log("Network Error: " + e.message);
        } finally {
            state.busy = false;
            els.sBtn.innerHTML = `<i class="fas fa-search"></i>`;
        }
    };

    const analyze = async () => {
        if (!state.u || state.busy) return;
        const h = window.IGHandler || IGHandler;
        
        state.busy = true;
        els.cBtn.innerHTML = `<i class="fas fa-sync fa-spin"></i> Indexing...`;
        
        try {
            const [fRes, fwRes] = await Promise.all([h.getFollowers(state.u), h.getFollowing(state.u)]);
            state.fws = Array.isArray(fRes) ? fRes : fRes?.items || fRes?.data || [];
            state.fwg = Array.isArray(fwRes) ? fwRes : fwRes?.items || fwRes?.data || [];

            const fSet = new Set(state.fws.map(f => (f.username || f.pk || '').toString().toLowerCase()));
            const nfs = state.fwg.filter(f => {
                const un = (f.username || f.pk || '').toString().toLowerCase();
                return !fSet.has(un) && !wl.has(un);
            }).sort((a,b) => (b.is_verified || 0) - (a.is_verified || 0));

            els.nTitle.innerHTML = nfs.length ? `Found ${nfs.length} Accounts` : `Audit Complete: 100% Retention`;
            els.nList.innerHTML = nfs.map(u => `
                <div class="user-card" style="display:flex; align-items:center; padding:10px; border-bottom:1px solid #334155;">
                    <img src="${esc(u.profile_pic_url || u.avatar)}" style="width:40px; height:40px; border-radius:50%; margin-right:12px;">
                    <div style="flex:1">
                        <div style="font-weight:bold; font-size:0.9rem">${esc(u.username)} ${u.is_verified ? '✔️' : ''}</div>
                        <div style="font-size:0.75rem; color:#94a3b8">${esc(u.full_name || '')}</div>
                    </div>
                    <a href="https://instagram.com/${esc(u.username)}" target="_blank" style="background:#334155; padding:5px 10px; border-radius:5px; font-size:0.7rem">View</a>
                </div>
            `).join('');

            els.rCon.style.display = 'block';
            if(els.xBtn) els.xBtn.style.display = nfs.length ? 'block' : 'none';
        } catch (e) {
            log("Analysis Failed: Check API limits or Session.");
        } finally {
            state.busy = false;
            els.cBtn.innerHTML = `<i class="fas fa-user-slash"></i> Run Full Audit`;
        }
    };

    els.sBtn.addEventListener('click', fetchP);
    els.cBtn.addEventListener('click', analyze);
    els.uIn.addEventListener('keypress', e => e.key === 'Enter' && fetchP());
    
    if (els.xBtn) {
        els.xBtn.addEventListener('click', () => {
            const csv = "username,full_name,url\n" + state.fwg.filter(f => !new Set(state.fws.map(x=>x.username)).has(f.username)).map(u => `${u.username},${u.full_name},https://instagram.com/${u.username}`).join('\n');
            const blob = new Blob([csv], {type:'text/csv'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url; a.download = `audit_${state.u}.csv`; a.click();
        });
    }
})();