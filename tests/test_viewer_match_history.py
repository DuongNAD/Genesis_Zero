"""Run the real viewer in the existing Node/Three.js harness."""

from test_challenger_m4_scrubber import _run_node_script


def test_match_transition_does_not_overwrite_same_tick():
    result = _run_node_script("""
      const h = createHarness();
      h.pushFrame({match_id: 'A', schema_version: '1.0', t: 0, creatures: []});
      const previous = h.sandbox.window.Genesis3D.historyBuffer;
      h.pushFrame({match_id: 'B', schema_version: '1.0', t: 0, creatures: []});
      const current = h.sandbox.window.Genesis3D.historyBuffer;
      console.log(JSON.stringify({
        previous: previous.map(f => f.match_id),
        current: current.map(f => f.match_id)
      }));
    """)
    assert result["previous"] == ["A"]
    assert result["current"] == ["B"]


def test_history_aliases_eviction_and_legacy():
    result = _run_node_script("""
      const {FrameHistory} = require('./web/frame_history.js');
      const h = new FrameHistory({maxFrames: 2, maxMatches: 2});
      const changes = [];
      const off = h.onMatchChanged((id, prev) => changes.push([id, prev]));
      h.add({match_id:'A', t:0, surface_map:['P'], creatures:[{
        id:'x', species_id:'custom', generation:7, energy:8,
        traits:{energy_max:42}, dt_traits:[1]}]});
      const c = h.getFrame('A',0).creatures[0];
      h.add({match_id:'A',t:2}); h.add({match_id:'A',t:1});
      h.add({match_id:'B',t:0});
      const stale = h.add({match_id:'A',t:0});
      off(); h.add({t:0});
      console.log(JSON.stringify({c, stale, changes,
        evicted:h.getFrame('A',0), matches:h.matches.size,
        legacy:h.getFrame('legacy',0).schema_version,
        terrain:h.getFrame('B',0).terrain}));
    """)
    assert result['c']['species'] == 'custom'
    assert result['c']['gen'] == 7
    assert result['c']['e_max'] == 42
    assert result['c']['d_tr'] == [1]
    assert result['stale'] is None
    assert result['evicted'] is None
    assert result['matches'] == 2
    assert result['legacy'] == 'legacy'
    assert result['terrain'] is None
    assert result['changes'] == [['A', None], ['B', 'A']]


def test_transition_resets_paused_view_and_hud():
    result = _run_node_script("""
      const h = createHarness();
      const api = h.sandbox.window.Genesis3D;
      api.onFrame({match_id:'A',schema_version:'1.0',t:80,creatures:[]});
      h.getEl('btn-playback-toggle').dispatchEvent({type:'click'});
      h.getEl('reveal-modal').style.display = 'flex';
      h.getEl('reveal-laws-list').textContent = 'old law';
      api.onFrame({match_id:'B',schema_version:'1.1',t:0,creatures:[]});
      console.log(JSON.stringify({
        match:h.getEl('match-id').textContent,
        schema:h.getEl('schema-version').textContent,
        min:h.getEl('timeline-slider').min, max:h.getEl('timeline-slider').max,
        tick:h.getEl('tick').textContent,
        modal:h.getEl('reveal-modal').style.display,
        laws:h.getEl('reveal-laws-list').textContent,
        old:api.getFrame('A',80).match_id, ids:api.entityIds
      }));
    """)
    assert result == dict(match='B', schema='1.1', min=0, max=0, tick=0,
                          modal='none', laws='', old='A', ids=[])



def test_real_entities_removed_on_transition_and_rewind():
    result = _run_node_script("""
      const h = createHarness(), api = h.sandbox.window.Genesis3D;
      const c = {id:'same',species:'custom',x:1,y:1,hp:50,e:80,e_max:100,
                 alive:true,tr:[2,2,2,2,2,2]};
      api.onFrame({match_id:'A',t:0,creatures:[c]});
      const initial = api.entityIds;
      api.onFrame({match_id:'B',t:0,creatures:[]});
      const empty = api.entityIds;
      api.onFrame({match_id:'B',t:5,creatures:[c]});
      h.getEl('timeline-slider').dispatchEvent({type:'input',target:{value:'0'}});
      console.log(JSON.stringify({initial,empty,rewound:api.entityIds}));
    """)
    assert result == dict(initial=['same'], empty=[], rewound=[])


def test_canvas_html_bootstrap_transition_and_scrub():
    result = _run_node_script("""
      const html = fs.readFileSync('web/watch.html','utf8');
      const ids = [...html.matchAll(/id="([^"]+)"/g)].map(m => m[1]);
      const elements = new Map();
      const calls = [];
      const ctx = new Proxy({}, {get: (_, key) => (...args) => calls.push([key,...args])});
      for (const id of ids) elements.set(id, {
        width:720,height:720,style:{},textContent:'',childNodes:[],
        getContext:()=>ctx,
        addEventListener(type,fn) {this[type]=fn;}
      });
      let ws, draw;
      const sandbox = {window:{location:{protocol:'http:',host:'localhost'}},
        document:{getElementById:id=>elements.get(id)},
        performance:{now:()=>0},setTimeout:()=>{},
        requestAnimationFrame:fn=>{draw=fn;},
        WebSocket:class {constructor(){ws=this;}}};
      vm.createContext(sandbox);
      for (const m of html.matchAll(/<script src="([^"]+)"/g)) {
        vm.runInContext(fs.readFileSync('web/'+m[1],'utf8'),sandbox);
      }
      const send = f => ws.onmessage({data:JSON.stringify(f)});
      const c = {id:'a',species:'custom',x:0,y:0,e:5,e_max:10,alive:true};
      send({match_id:'A',schema_version:'1.0',t:0,terrain:['W'],creatures:[c]});
      draw();
      const before = calls.filter(c=>c[0]==='ellipse').length;
      send({match_id:'B',schema_version:'1.1',t:0,creatures:[]});
      calls.length=0; draw();
      const after = calls.filter(c=>c[0]==='ellipse').length;
      send({match_id:'B',schema_version:'1.1',t:5,creatures:[c]});
      const slider=elements.get('timeline-slider');
      slider.input({target:{value:'0'}});
      console.log(JSON.stringify({before,after,
        tick:elements.get('tick-val').textContent,
        match:elements.get('match-id').textContent,
        schema:elements.get('schema-version').textContent,
        terrain:sandbox.window.Genesis2D.terrain,
        min:slider.min,max:slider.max}));
    """)
    assert result == dict(before=1, after=0, tick=0, match='B', schema='1.1',
                          terrain=None, min=0, max=5)


def test_real_workload_fifo_survives_serialized_history_reload():
    result = _run_node_script("""
      const assert = require('node:assert/strict');
      const {FrameHistory} = require('./web/frame_history.js');
      const history = new FrameHistory();
      const expected = [];
      for (let t = 0; t <= 5000; t++) {
        const frame = history.add({
          match_id:'workload', schema_version:'1.0', t, phase:'RUNNING',
          w:2, h:2, ...(t === 0 ? {terrain:['PW','BP']} : {}),
          weather:{state:'CLEAR',diurnal:'DAY',progress:(t % 100)/100},
          creatures:[0,1].map(i => ({
            id:`custom:${i}`,species:'custom',x:(t+i)%2,y:i,
            hp:100-t%30,e:80-t%20,e_max:100,alive:true,
            tr:[2,3,2,3,1,2],gen:Math.floor(t/100),features:['TUI_MA'],
            parent_id:null,lineage:'custom:0',age:t,d_tr:[0,1,0,1,-1,0]
          })),
          plants:[[t%2,0]],corpses:[],
          events:[{k:'EAT',who:'custom:0',pos:[t%2,0]}]
        });
        if (t >= 4900) expected.push(frame);
      }
      const serialized = JSON.stringify(history.frames());
      const restored = new FrameHistory();
      for (const frame of JSON.parse(serialized)) restored.add(frame);
      for (const store of [history, restored]) {
        assert.equal(store.frames().length,1200);
        assert.equal(store.matches.get('workload').byTick.size,1200);
        assert.deepEqual(store.frames().map(f=>f.t),
          Array.from({length:1200},(_,i)=>3801+i));
        for (let t=0;t<3801;t++) assert.equal(store.getFrame('workload',t),null);
        assert.deepEqual(Array.from({length:101},(_,i)=>
          store.getFrame('workload',4900+i)),expected);
      }
      console.log(JSON.stringify({retained:restored.frames().length,verified:expected.length}));
    """)
    assert result == {"retained": 1200, "verified": 101}

