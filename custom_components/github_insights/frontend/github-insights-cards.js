const definitions = [
    {
        kind: "insights",
        tag: "github-insights-card",
        editorTag: "github-insights-card-editor",
        name: "GitHub Insights",
        description: "Configurable account, usage, Actions, Copilot, activity, contributions, and security insights.",
        icon: "mdi:github",
        defaultMetrics: [
            "account",
            "actions_configured_included_minutes",
            "actions_configured_minutes_used_percent",
            "actions_configured_minutes_remaining",
            "actions_gross_cost",
            "actions_discount",
            "actions_cost",
            "actions_budget_percent",
            "copilot_paid_usage",
            "public_repositories",
            "open_pull_requests",
            "workflow_health",
            "dependabot_alerts",
            "commits",
            "contributions",
            "last_successful_sync",
        ],
        defaultSections: [
            "overview",
            "usage",
            "actions",
            "copilot",
            "activity",
            "contributions",
            "security",
        ],
        defaultLayout: "expanded",
    },
    {
        kind: "repository",
        tag: "github-insights-repository-card",
        editorTag: "github-insights-repository-card-editor",
        name: "GitHub Insights repository",
        description: "Configurable collection or detail view for discovered repositories.",
        icon: "mdi:source-repository-multiple",
        defaultMetrics: [
            "stars",
            "forks",
            "open_issues",
            "open_pull_requests",
            "workflow_health",
            "actions_usage_percent",
        ],
        defaultSections: [],
        defaultLayout: "responsive",
    },
];
const CARD_DEFINITIONS = definitions;
const INSIGHTS_SECTIONS = [
    "overview",
    "usage",
    "actions",
    "copilot",
    "activity",
    "contributions",
    "security",
];
const PRESET_CONFIGS = {
    overview: {
        metrics: [
            "account",
            "actions_configured_minutes_used_percent",
            "actions_configured_minutes_remaining",
            "actions_cost",
            "copilot_paid_usage",
            "public_repositories",
            "open_pull_requests",
            "workflow_health",
            "dependabot_alerts",
            "last_successful_sync",
        ],
        sections: ["overview", "usage", "actions", "copilot", "security"],
        layout: "responsive",
    },
    usage: {
        metrics: [
            "actions_configured_included_minutes",
            "actions_configured_minutes_used",
            "actions_configured_minutes_remaining",
            "actions_configured_minutes_used_percent",
            "actions_gross_cost",
            "actions_discount",
            "actions_cost",
            "actions_discounted_usage",
            "actions_billable_usage",
            "actions_budget",
            "actions_budget_remaining",
            "actions_budget_percent",
            "actions_blocked",
            "actions_estimated_minutes_remaining",
            "billing_period",
            "copilot_paid_usage",
        ],
        sections: ["usage", "actions", "copilot"],
        layout: "expanded",
    },
    actions: {
        metrics: [
            "actions_configured_included_minutes",
            "actions_configured_minutes_used",
            "actions_configured_minutes_remaining",
            "actions_configured_minutes_used_percent",
            "actions_gross_cost",
            "actions_discount",
            "actions_cost",
            "workflow_health",
            "actions_discounted_usage",
            "actions_billable_usage",
            "actions_budget",
            "actions_budget_remaining",
            "actions_budget_percent",
            "actions_blocked",
            "actions_estimated_minutes_remaining",
            "billing_period",
        ],
        sections: ["usage", "actions"],
        layout: "responsive",
    },
    copilot: {
        metrics: [
            "copilot_paid_usage",
            "copilot_cost",
            "copilot_active_users",
            "last_successful_sync",
        ],
        sections: ["copilot", "overview"],
        layout: "responsive",
    },
    activity: {
        metrics: [
            "commits",
            "pull_requests_opened",
            "pull_requests_merged",
            "issues_opened",
            "reviews",
            "releases",
        ],
        sections: ["activity"],
        layout: "responsive",
    },
    contributions: {
        metrics: ["contributions", "current_streak", "longest_streak"],
        sections: ["contributions"],
        layout: "responsive",
    },
    security: {
        metrics: [
            "dependabot_alerts",
            "code_scanning_alerts",
            "secret_scanning_alerts",
            "last_successful_sync",
        ],
        sections: ["security", "overview"],
        layout: "responsive",
    },
    dashboard: {
        metrics: definitions[0].defaultMetrics,
        sections: definitions[0].defaultSections,
        layout: "expanded",
    },
    compact: {
        metrics: [
            "actions_configured_minutes_used_percent",
            "actions_budget_remaining",
        ],
        sections: ["usage", "actions"],
        layout: "compact",
    },
};

/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t$1=globalThis,e$2=t$1.ShadowRoot&&(void 0===t$1.ShadyCSS||t$1.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,s$2=Symbol(),o$3=new WeakMap;let n$2 = class n{constructor(t,e,o){if(this._$cssResult$=true,o!==s$2)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e;}get styleSheet(){let t=this.o;const s=this.t;if(e$2&&void 0===t){const e=void 0!==s&&1===s.length;e&&(t=o$3.get(s)),void 0===t&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),e&&o$3.set(s,t));}return t}toString(){return this.cssText}};const r$2=t=>new n$2("string"==typeof t?t:t+"",void 0,s$2),i$3=(t,...e)=>{const o=1===t.length?t[0]:e.reduce((e,s,o)=>e+(t=>{if(true===t._$cssResult$)return t.cssText;if("number"==typeof t)return t;throw Error("Value passed to 'css' function must be a 'css' function result: "+t+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(s)+t[o+1],t[0]);return new n$2(o,t,s$2)},S$1=(s,o)=>{if(e$2)s.adoptedStyleSheets=o.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const e of o){const o=document.createElement("style"),n=t$1.litNonce;void 0!==n&&o.setAttribute("nonce",n),o.textContent=e.cssText,s.appendChild(o);}},c$2=e$2?t=>t:t=>t instanceof CSSStyleSheet?(t=>{let e="";for(const s of t.cssRules)e+=s.cssText;return r$2(e)})(t):t;

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const{is:i$2,defineProperty:e$1,getOwnPropertyDescriptor:h$1,getOwnPropertyNames:r$1,getOwnPropertySymbols:o$2,getPrototypeOf:n$1}=Object,a$1=globalThis,c$1=a$1.trustedTypes,l$1=c$1?c$1.emptyScript:"",p$1=a$1.reactiveElementPolyfillSupport,d$1=(t,s)=>t,u$1={toAttribute(t,s){switch(s){case Boolean:t=t?l$1:null;break;case Object:case Array:t=null==t?t:JSON.stringify(t);}return t},fromAttribute(t,s){let i=t;switch(s){case Boolean:i=null!==t;break;case Number:i=null===t?null:Number(t);break;case Object:case Array:try{i=JSON.parse(t);}catch(t){i=null;}}return i}},f$1=(t,s)=>!i$2(t,s),b$1={attribute:true,type:String,converter:u$1,reflect:false,useDefault:false,hasChanged:f$1};Symbol.metadata??=Symbol("metadata"),a$1.litPropertyMetadata??=new WeakMap;let y$1 = class y extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t);}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,s=b$1){if(s.state&&(s.attribute=false),this._$Ei(),this.prototype.hasOwnProperty(t)&&((s=Object.create(s)).wrapped=true),this.elementProperties.set(t,s),!s.noAccessor){const i=Symbol(),h=this.getPropertyDescriptor(t,i,s);void 0!==h&&e$1(this.prototype,t,h);}}static getPropertyDescriptor(t,s,i){const{get:e,set:r}=h$1(this.prototype,t)??{get(){return this[s]},set(t){this[s]=t;}};return {get:e,set(s){const h=e?.call(this);r?.call(this,s),this.requestUpdate(t,h,i);},configurable:true,enumerable:true}}static getPropertyOptions(t){return this.elementProperties.get(t)??b$1}static _$Ei(){if(this.hasOwnProperty(d$1("elementProperties")))return;const t=n$1(this);t.finalize(),void 0!==t.l&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties);}static finalize(){if(this.hasOwnProperty(d$1("finalized")))return;if(this.finalized=true,this._$Ei(),this.hasOwnProperty(d$1("properties"))){const t=this.properties,s=[...r$1(t),...o$2(t)];for(const i of s)this.createProperty(i,t[i]);}const t=this[Symbol.metadata];if(null!==t){const s=litPropertyMetadata.get(t);if(void 0!==s)for(const[t,i]of s)this.elementProperties.set(t,i);}this._$Eh=new Map;for(const[t,s]of this.elementProperties){const i=this._$Eu(t,s);void 0!==i&&this._$Eh.set(i,t);}this.elementStyles=this.finalizeStyles(this.styles);}static finalizeStyles(s){const i=[];if(Array.isArray(s)){const e=new Set(s.flat(1/0).reverse());for(const s of e)i.unshift(c$2(s));}else void 0!==s&&i.push(c$2(s));return i}static _$Eu(t,s){const i=s.attribute;return  false===i?void 0:"string"==typeof i?i:"string"==typeof t?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=false,this.hasUpdated=false,this._$Em=null,this._$Ev();}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this));}addController(t){(this._$EO??=new Set).add(t),void 0!==this.renderRoot&&this.isConnected&&t.hostConnected?.();}removeController(t){this._$EO?.delete(t);}_$E_(){const t=new Map,s=this.constructor.elementProperties;for(const i of s.keys())this.hasOwnProperty(i)&&(t.set(i,this[i]),delete this[i]);t.size>0&&(this._$Ep=t);}createRenderRoot(){const t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return S$1(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(true),this._$EO?.forEach(t=>t.hostConnected?.());}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.());}attributeChangedCallback(t,s,i){this._$AK(t,i);}_$ET(t,s){const i=this.constructor.elementProperties.get(t),e=this.constructor._$Eu(t,i);if(void 0!==e&&true===i.reflect){const h=(void 0!==i.converter?.toAttribute?i.converter:u$1).toAttribute(s,i.type);this._$Em=t,null==h?this.removeAttribute(e):this.setAttribute(e,h),this._$Em=null;}}_$AK(t,s){const i=this.constructor,e=i._$Eh.get(t);if(void 0!==e&&this._$Em!==e){const t=i.getPropertyOptions(e),h="function"==typeof t.converter?{fromAttribute:t.converter}:void 0!==t.converter?.fromAttribute?t.converter:u$1;this._$Em=e;const r=h.fromAttribute(s,t.type);this[e]=r??this._$Ej?.get(e)??r,this._$Em=null;}}requestUpdate(t,s,i,e=false,h){if(void 0!==t){const r=this.constructor;if(false===e&&(h=this[t]),i??=r.getPropertyOptions(t),!((i.hasChanged??f$1)(h,s)||i.useDefault&&i.reflect&&h===this._$Ej?.get(t)&&!this.hasAttribute(r._$Eu(t,i))))return;this.C(t,s,i);} false===this.isUpdatePending&&(this._$ES=this._$EP());}C(t,s,{useDefault:i,reflect:e,wrapped:h},r){i&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,r??s??this[t]),true!==h||void 0!==r)||(this._$AL.has(t)||(this.hasUpdated||i||(s=void 0),this._$AL.set(t,s)),true===e&&this._$Em!==t&&(this._$Eq??=new Set).add(t));}async _$EP(){this.isUpdatePending=true;try{await this._$ES;}catch(t){Promise.reject(t);}const t=this.scheduleUpdate();return null!=t&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[t,s]of this._$Ep)this[t]=s;this._$Ep=void 0;}const t=this.constructor.elementProperties;if(t.size>0)for(const[s,i]of t){const{wrapped:t}=i,e=this[s];true!==t||this._$AL.has(s)||void 0===e||this.C(s,void 0,i,e);}}let t=false;const s=this._$AL;try{t=this.shouldUpdate(s),t?(this.willUpdate(s),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(s)):this._$EM();}catch(s){throw t=false,this._$EM(),s}t&&this._$AE(s);}willUpdate(t){}_$AE(t){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=true,this.firstUpdated(t)),this.updated(t);}_$EM(){this._$AL=new Map,this.isUpdatePending=false;}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return  true}update(t){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM();}updated(t){}firstUpdated(t){}};y$1.elementStyles=[],y$1.shadowRootOptions={mode:"open"},y$1[d$1("elementProperties")]=new Map,y$1[d$1("finalized")]=new Map,p$1?.({ReactiveElement:y$1}),(a$1.reactiveElementVersions??=[]).push("2.1.2");

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */
const t=globalThis,i$1=t=>t,s$1=t.trustedTypes,e=s$1?s$1.createPolicy("lit-html",{createHTML:t=>t}):void 0,h="$lit$",o$1=`lit$${Math.random().toFixed(9).slice(2)}$`,n="?"+o$1,r=`<${n}>`,l=document,c=()=>l.createComment(""),a=t=>null===t||"object"!=typeof t&&"function"!=typeof t,u=Array.isArray,d=t=>u(t)||"function"==typeof t?.[Symbol.iterator],f="[ \t\n\f\r]",v=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,_=/-->/g,m=/>/g,p=RegExp(`>|${f}(?:([^\\s"'>=/]+)(${f}*=${f}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`,"g"),g=/'/g,$=/"/g,y=/^(?:script|style|textarea|title)$/i,x=t=>(i,...s)=>({_$litType$:t,strings:i,values:s}),b=x(1),E=Symbol.for("lit-noChange"),A=Symbol.for("lit-nothing"),C=new WeakMap,P=l.createTreeWalker(l,129);function V(t,i){if(!u(t)||!t.hasOwnProperty("raw"))throw Error("invalid template strings array");return void 0!==e?e.createHTML(i):i}const N=(t,i)=>{const s=t.length-1,e=[];let n,l=2===i?"<svg>":3===i?"<math>":"",c=v;for(let i=0;i<s;i++){const s=t[i];let a,u,d=-1,f=0;for(;f<s.length&&(c.lastIndex=f,u=c.exec(s),null!==u);)f=c.lastIndex,c===v?"!--"===u[1]?c=_:void 0!==u[1]?c=m:void 0!==u[2]?(y.test(u[2])&&(n=RegExp("</"+u[2],"g")),c=p):void 0!==u[3]&&(c=p):c===p?">"===u[0]?(c=n??v,d=-1):void 0===u[1]?d=-2:(d=c.lastIndex-u[2].length,a=u[1],c=void 0===u[3]?p:'"'===u[3]?$:g):c===$||c===g?c=p:c===_||c===m?c=v:(c=p,n=void 0);const x=c===p&&t[i+1].startsWith("/>")?" ":"";l+=c===v?s+r:d>=0?(e.push(a),s.slice(0,d)+h+s.slice(d)+o$1+x):s+o$1+(-2===d?i:x);}return [V(t,l+(t[s]||"<?>")+(2===i?"</svg>":3===i?"</math>":"")),e]};class S{constructor({strings:t,_$litType$:i},e){let r;this.parts=[];let l=0,a=0;const u=t.length-1,d=this.parts,[f,v]=N(t,i);if(this.el=S.createElement(f,e),P.currentNode=this.el.content,2===i||3===i){const t=this.el.content.firstChild;t.replaceWith(...t.childNodes);}for(;null!==(r=P.nextNode())&&d.length<u;){if(1===r.nodeType){if(r.hasAttributes())for(const t of r.getAttributeNames())if(t.endsWith(h)){const i=v[a++],s=r.getAttribute(t).split(o$1),e=/([.?@])?(.*)/.exec(i);d.push({type:1,index:l,name:e[2],strings:s,ctor:"."===e[1]?I:"?"===e[1]?L:"@"===e[1]?z:H}),r.removeAttribute(t);}else t.startsWith(o$1)&&(d.push({type:6,index:l}),r.removeAttribute(t));if(y.test(r.tagName)){const t=r.textContent.split(o$1),i=t.length-1;if(i>0){r.textContent=s$1?s$1.emptyScript:"";for(let s=0;s<i;s++)r.append(t[s],c()),P.nextNode(),d.push({type:2,index:++l});r.append(t[i],c());}}}else if(8===r.nodeType)if(r.data===n)d.push({type:2,index:l});else {let t=-1;for(;-1!==(t=r.data.indexOf(o$1,t+1));)d.push({type:7,index:l}),t+=o$1.length-1;}l++;}}static createElement(t,i){const s=l.createElement("template");return s.innerHTML=t,s}}function M(t,i,s=t,e){if(i===E)return i;let h=void 0!==e?s._$Co?.[e]:s._$Cl;const o=a(i)?void 0:i._$litDirective$;return h?.constructor!==o&&(h?._$AO?.(false),void 0===o?h=void 0:(h=new o(t),h._$AT(t,s,e)),void 0!==e?(s._$Co??=[])[e]=h:s._$Cl=h),void 0!==h&&(i=M(t,h._$AS(t,i.values),h,e)),i}class R{constructor(t,i){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=i;}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){const{el:{content:i},parts:s}=this._$AD,e=(t?.creationScope??l).importNode(i,true);P.currentNode=e;let h=P.nextNode(),o=0,n=0,r=s[0];for(;void 0!==r;){if(o===r.index){let i;2===r.type?i=new k(h,h.nextSibling,this,t):1===r.type?i=new r.ctor(h,r.name,r.strings,this,t):6===r.type&&(i=new Z(h,this,t)),this._$AV.push(i),r=s[++n];}o!==r?.index&&(h=P.nextNode(),o++);}return P.currentNode=l,e}p(t){let i=0;for(const s of this._$AV) void 0!==s&&(void 0!==s.strings?(s._$AI(t,s,i),i+=s.strings.length-2):s._$AI(t[i])),i++;}}class k{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,i,s,e){this.type=2,this._$AH=A,this._$AN=void 0,this._$AA=t,this._$AB=i,this._$AM=s,this.options=e,this._$Cv=e?.isConnected??true;}get parentNode(){let t=this._$AA.parentNode;const i=this._$AM;return void 0!==i&&11===t?.nodeType&&(t=i.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,i=this){t=M(this,t,i),a(t)?t===A||null==t||""===t?(this._$AH!==A&&this._$AR(),this._$AH=A):t!==this._$AH&&t!==E&&this._(t):void 0!==t._$litType$?this.$(t):void 0!==t.nodeType?this.T(t):d(t)?this.k(t):this._(t);}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t));}_(t){this._$AH!==A&&a(this._$AH)?this._$AA.nextSibling.data=t:this.T(l.createTextNode(t)),this._$AH=t;}$(t){const{values:i,_$litType$:s}=t,e="number"==typeof s?this._$AC(t):(void 0===s.el&&(s.el=S.createElement(V(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===e)this._$AH.p(i);else {const t=new R(e,this),s=t.u(this.options);t.p(i),this.T(s),this._$AH=t;}}_$AC(t){let i=C.get(t.strings);return void 0===i&&C.set(t.strings,i=new S(t)),i}k(t){u(this._$AH)||(this._$AH=[],this._$AR());const i=this._$AH;let s,e=0;for(const h of t)e===i.length?i.push(s=new k(this.O(c()),this.O(c()),this,this.options)):s=i[e],s._$AI(h),e++;e<i.length&&(this._$AR(s&&s._$AB.nextSibling,e),i.length=e);}_$AR(t=this._$AA.nextSibling,s){for(this._$AP?.(false,true,s);t!==this._$AB;){const s=i$1(t).nextSibling;i$1(t).remove(),t=s;}}setConnected(t){ void 0===this._$AM&&(this._$Cv=t,this._$AP?.(t));}}class H{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,i,s,e,h){this.type=1,this._$AH=A,this._$AN=void 0,this.element=t,this.name=i,this._$AM=e,this.options=h,s.length>2||""!==s[0]||""!==s[1]?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=A;}_$AI(t,i=this,s,e){const h=this.strings;let o=false;if(void 0===h)t=M(this,t,i,0),o=!a(t)||t!==this._$AH&&t!==E,o&&(this._$AH=t);else {const e=t;let n,r;for(t=h[0],n=0;n<h.length-1;n++)r=M(this,e[s+n],i,n),r===E&&(r=this._$AH[n]),o||=!a(r)||r!==this._$AH[n],r===A?t=A:t!==A&&(t+=(r??"")+h[n+1]),this._$AH[n]=r;}o&&!e&&this.j(t);}j(t){t===A?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"");}}class I extends H{constructor(){super(...arguments),this.type=3;}j(t){this.element[this.name]=t===A?void 0:t;}}class L extends H{constructor(){super(...arguments),this.type=4;}j(t){this.element.toggleAttribute(this.name,!!t&&t!==A);}}class z extends H{constructor(t,i,s,e,h){super(t,i,s,e,h),this.type=5;}_$AI(t,i=this){if((t=M(this,t,i,0)??A)===E)return;const s=this._$AH,e=t===A&&s!==A||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,h=t!==A&&(s===A||e);e&&this.element.removeEventListener(this.name,this,s),h&&this.element.addEventListener(this.name,this,t),this._$AH=t;}handleEvent(t){"function"==typeof this._$AH?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t);}}class Z{constructor(t,i,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=i,this.options=s;}get _$AU(){return this._$AM._$AU}_$AI(t){M(this,t);}}const B=t.litHtmlPolyfillSupport;B?.(S,k),(t.litHtmlVersions??=[]).push("3.3.3");const D=(t,i,s)=>{const e=s?.renderBefore??i;let h=e._$litPart$;if(void 0===h){const t=s?.renderBefore??null;e._$litPart$=h=new k(i.insertBefore(c(),t),t,void 0,s??{});}return h._$AI(t),h};

/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const s=globalThis;class i extends y$1{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0;}createRenderRoot(){const t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){const r=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=D(r,this.renderRoot,this.renderOptions);}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(true);}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(false);}render(){return E}}i._$litElement$=true,i["finalized"]=true,s.litElementHydrateSupport?.({LitElement:i});const o=s.litElementPolyfillSupport;o?.({LitElement:i});(s.litElementVersions??=[]).push("4.2.2");

const metric = (key, label, icon, format, group, estimated = false, sourceLabel, prominent = false) => ({
    key,
    label,
    icon,
    format,
    group,
    estimated,
    sourceLabel,
    prominent,
});
const METRICS = Object.fromEntries([
    metric("account", "Account", "mdi:github", "text", "account"),
    metric("public_repositories", "Public repositories", "mdi:source-repository", "number", "repositories"),
    metric("private_repositories", "Private repositories", "mdi:lock", "number", "repositories"),
    metric("repositories", "Repositories", "mdi:source-repository-multiple", "number", "repositories"),
    metric("stars", "Stars", "mdi:star-outline", "number", "repositories"),
    metric("forks", "Forks", "mdi:source-fork", "number", "repositories"),
    metric("open_issues", "Open issues", "mdi:alert-circle-outline", "number", "repositories"),
    metric("open_pull_requests", "Open pull requests", "mdi:source-pull", "number", "repositories"),
    metric("latest_commit", "Latest commit", "mdi:source-commit", "text", "repositories"),
    metric("latest_release", "Latest release", "mdi:tag-outline", "text", "repositories"),
    metric("last_push", "Last push", "mdi:clock-outline", "datetime", "repositories"),
    metric("traffic_views", "Traffic views", "mdi:eye-outline", "number", "repositories"),
    metric("workflow_health", "Workflow health", "mdi:check-circle-outline", "text", "actions"),
    metric("actions_runtime", "Workflow runtime", "mdi:timer-outline", "duration", "actions"),
    metric("actions_discounted_usage", "Discounted or included consumption", "mdi:package-variant", "number", "actions"),
    metric("actions_billable_usage", "Paid usage", "mdi:cash-plus", "number", "actions"),
    metric("actions_minutes_remaining", "Actions remaining", "mdi:timer-sand", "number", "actions"),
    metric("actions_usage_percent", "Actions usage", "mdi:gauge", "percent", "actions"),
    metric("actions_configured_included_minutes", "Configured allowance", "mdi:timer-check-outline", "number", "actions", false, "Configured GitHub Actions allowance", true),
    metric("actions_configured_minutes_used", "Allowance used", "mdi:timer-play-outline", "number", "actions", false, "Configured allowance calculation", true),
    metric("actions_configured_minutes_remaining", "Allowance remaining", "mdi:timer-sand", "number", "actions", false, "Configured allowance calculation", true),
    metric("actions_configured_minutes_used_percent", "Allowance used", "mdi:gauge", "percent", "actions", false, "Configured allowance calculation", true),
    metric("actions_cost", "Net cost", "mdi:cash", "currency", "billing", false, "Authoritative GitHub billing", true),
    metric("actions_gross_cost", "Gross cost", "mdi:cash-multiple", "currency", "billing", false, "Authoritative GitHub billing", true),
    metric("actions_discount", "Discount", "mdi:sale", "currency", "billing", false, "Authoritative GitHub billing", true),
    metric("actions_budget", "GitHub-enforced budget", "mdi:shield-lock", "currency", "billing"),
    metric("actions_budget_remaining", "Budget remaining", "mdi:piggy-bank-outline", "currency", "billing"),
    metric("actions_budget_percent", "Budget utilization", "mdi:chart-donut", "percent", "billing"),
    metric("actions_budget_scope", "Budget scope", "mdi:target-account", "text", "billing"),
    metric("billing_period", "Billing period", "mdi:calendar-range", "text", "billing"),
    metric("actions_estimated_minutes_remaining", "Estimated equivalent minutes", "mdi:calculator-variant-outline", "number", "billing", true),
    metric("actions_stop_usage", "Stop usage enabled", "mdi:stop-circle-outline", "boolean", "billing"),
    metric("actions_budget_warning", "Budget warning", "mdi:alert-outline", "boolean", "billing"),
    metric("actions_budget_exhausted", "Budget exhausted", "mdi:alert-octagon-outline", "boolean", "billing"),
    metric("actions_blocked", "Actions blocked", "mdi:block-helper", "boolean", "billing"),
    metric("actions_failed_runs", "Failed runs", "mdi:close-circle-outline", "number", "actions"),
    metric("actions_recent_runs", "Recent runs", "mdi:history", "number", "actions"),
    metric("actions_forecast", "Actions forecast", "mdi:chart-line", "currency", "billing"),
    metric("artifact_storage", "Artifact storage", "mdi:archive-outline", "number", "billing"),
    metric("package_storage", "Package storage", "mdi:package-variant", "number", "billing"),
    metric("cache_usage", "Cache usage", "mdi:cached", "number", "billing"),
    metric("copilot_usage_percent", "AI usage", "mdi:robot-outline", "percent", "copilot"),
    metric("copilot_included_quantity", "Included AI usage", "mdi:package-variant-closed", "number", "copilot"),
    metric("copilot_paid_usage", "Paid AI usage", "mdi:cash-plus", "number", "copilot"),
    metric("copilot_remaining_quantity", "AI usage remaining", "mdi:counter", "number", "copilot"),
    metric("copilot_cost", "AI cost", "mdi:cash", "currency", "copilot"),
    metric("copilot_active_users", "Active Copilot users", "mdi:account-group-outline", "number", "copilot"),
    metric("commits", "Commits", "mdi:source-commit", "number", "activity"),
    metric("pull_requests_opened", "Pull requests opened", "mdi:source-pull", "number", "activity"),
    metric("pull_requests_merged", "Pull requests merged", "mdi:source-merge", "number", "activity"),
    metric("issues_opened", "Issues opened", "mdi:alert-circle-outline", "number", "activity"),
    metric("reviews", "Reviews", "mdi:comment-check-outline", "number", "activity"),
    metric("releases", "Releases", "mdi:tag-outline", "number", "activity"),
    metric("contributions", "Contributions", "mdi:chart-timeline-variant-shimmer", "number", "activity"),
    metric("current_streak", "Current reliable streak", "mdi:fire", "number", "activity"),
    metric("longest_streak", "Longest reliable streak", "mdi:trophy-outline", "number", "activity"),
    metric("dependabot_alerts", "Dependabot alerts", "mdi:robot-angry-outline", "number", "security"),
    metric("code_scanning_alerts", "Code scanning alerts", "mdi:shield-search", "number", "security"),
    metric("secret_scanning_alerts", "Secret scanning alerts", "mdi:key-alert-outline", "number", "security"),
    metric("api_rate_limit_remaining", "API requests remaining", "mdi:speedometer", "number", "diagnostic"),
    metric("last_successful_sync", "API freshness", "mdi:clock-check-outline", "datetime", "diagnostic"),
].map((entry) => [entry.key, entry]));
function metricDefinition(key) {
    return (METRICS[key] ?? {
        key,
        label: key.replaceAll("_", " ").replace(/^\w/, (value) => value.toUpperCase()),
        icon: "mdi:chart-box-outline",
        format: "text",
        group: "diagnostic",
    });
}

const DOMAIN = "github_insights";
function keyFromEntry(entry) {
    if (entry.translation_key)
        return entry.translation_key;
    const unique = entry.unique_id ?? "";
    const knownKey = Object.keys(METRICS)
        .sort((a, b) => b.length - a.length)
        .find((key) => unique === key || unique.endsWith(`_${key}`));
    if (knownKey)
        return knownKey;
    const separator = unique.indexOf("_");
    return separator >= 0 ? unique.slice(separator + 1) : unique;
}
class EntityDiscoveryService {
    static { this.cache = new WeakMap(); }
    static clearCache() {
        this.cache = new WeakMap();
    }
    static async discover(hass, config) {
        const explicit = Object.entries(config.entities ?? {}).map(([key, entityId]) => ({ key, entityId }));
        if (config.entity) {
            explicit.push({
                key: config.primary_metric ?? "primary",
                entityId: config.entity,
            });
        }
        if (explicit.length > 0)
            return explicit;
        if (!hass.connection)
            return [];
        const connection = hass.connection;
        let pending = this.cache.get(connection);
        if (!pending) {
            pending = this.load(hass);
            this.cache.set(connection, pending);
        }
        return pending;
    }
    static async load(hass) {
        const connection = hass.connection;
        if (!connection)
            return [];
        const [entities, devices] = await Promise.all([
            connection.sendMessagePromise({
                type: "config/entity_registry/list",
            }),
            connection
                .sendMessagePromise({
                type: "config/device_registry/list",
            })
                .catch(() => []),
        ]);
        const deviceNames = new Map(devices.map((device) => [
            device.id,
            device.name_by_user ?? device.name ?? undefined,
        ]));
        return entities
            .filter((entry) => entry.platform === DOMAIN &&
            entry.disabled_by !== "integration" &&
            Boolean(entry.entity_id))
            .map((entry) => ({
            key: keyFromEntry(entry),
            entityId: entry.entity_id,
            configEntryId: entry.config_entry_id,
            deviceId: entry.device_id,
            repository: entry.device_id
                ? deviceNames.get(entry.device_id)
                : undefined,
        }));
    }
}
function entitiesByKey(discovered) {
    const result = new Map();
    for (const entity of discovered) {
        if (!result.has(entity.key))
            result.set(entity.key, entity);
    }
    return result;
}

const cardStyles = i$3 `
  :host {
    display: block;
    color: var(--primary-text-color);
    --gi-gap: 12px;
    --gi-soft: color-mix(in srgb, var(--primary-color) 11%, transparent);
    --gi-warning: var(--warning-color, #f59e0b);
    --gi-critical: var(--error-color, #db4437);
    --gi-success: var(--success-color, #43a047);
  }

  ha-card {
    overflow: hidden;
    border-radius: var(--ha-card-border-radius, 16px);
    box-shadow: var(--ha-card-box-shadow);
    background: var(--card-background-color);
  }

  .card {
    padding: 16px;
  }

  .header,
  .account,
  .metric-heading,
  .status,
  .actions {
    display: flex;
    align-items: center;
  }

  .header {
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 14px;
  }

  h2 {
    margin: 0;
    font-size: 1.15rem;
    line-height: 1.35;
  }

  h3 {
    margin: 16px 0 8px;
    font-size: 0.9rem;
    text-transform: capitalize;
  }

  .metric-section:first-of-type h3 {
    margin-top: 0;
  }

  .subtitle,
  .label,
  .meta,
  .empty {
    color: var(--secondary-text-color);
  }

  .account {
    gap: 10px;
    min-width: 0;
  }

  .account img {
    flex: 0 0 auto;
    border-radius: 50%;
  }

  .subtitle,
  .meta {
    font-size: 0.78rem;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(145px, 100%), 1fr));
    gap: var(--gi-gap);
  }

  :host([layout="compact"]) .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }

  .metric,
  .module,
  .repository {
    min-width: 0;
    padding: 12px;
    border-radius: calc(var(--ha-card-border-radius, 16px) * 0.72);
    background: var(--gi-soft);
    border: 1px solid color-mix(in srgb, var(--divider-color) 68%, transparent);
  }

  .metric.prominent {
    border-color: color-mix(in srgb, var(--primary-color) 45%, var(--divider-color));
    background: color-mix(in srgb, var(--primary-color) 15%, var(--card-background-color));
  }

  .metric-heading {
    gap: 7px;
    min-height: 24px;
  }

  .metric-link,
  .repository a {
    color: var(--primary-text-color);
    font-weight: 650;
    text-decoration-thickness: 1px;
    text-underline-offset: 3px;
  }

  ha-icon {
    color: var(--state-icon-color, var(--primary-color));
    --mdc-icon-size: 20px;
  }

  .value {
    display: block;
    margin-top: 7px;
    font-size: 1.25rem;
    font-weight: 650;
    overflow-wrap: anywhere;
  }

  .metric.warning {
    --gi-soft: color-mix(in srgb, var(--gi-warning) 14%, transparent);
  }

  .metric.critical {
    --gi-soft: color-mix(in srgb, var(--gi-critical) 16%, transparent);
  }

  .metric.healthy {
    --gi-soft: color-mix(in srgb, var(--gi-success) 11%, transparent);
  }

  .metric.unavailable {
    opacity: 0.72;
  }

  .bar {
    height: 6px;
    margin-top: 10px;
    overflow: hidden;
    border-radius: 999px;
    background: color-mix(in srgb, var(--divider-color) 70%, transparent);
  }

  .bar > span {
    display: block;
    height: 100%;
    width: var(--progress, 0%);
    max-width: 100%;
    border-radius: inherit;
    background: var(--primary-color);
    transition: width 180ms ease-out;
  }

  svg {
    display: block;
    width: 100%;
    height: 32px;
    margin-top: 8px;
    color: var(--primary-color);
  }

  .status {
    gap: 8px;
    padding: 12px;
    border-radius: 12px;
    background: color-mix(in srgb, var(--divider-color) 35%, transparent);
  }

  .status.error,
  .status.blocked {
    background: color-mix(in srgb, var(--gi-critical) 15%, transparent);
  }

  .status.warning {
    background: color-mix(in srgb, var(--gi-warning) 15%, transparent);
  }

  .repositories {
    display: grid;
    gap: 8px;
    margin-top: 12px;
  }

  .repository {
    display: block;
    gap: 8px;
  }

  .repository-heading {
    display: grid;
    grid-template-columns: auto minmax(0, 1fr) auto;
    align-items: center;
    gap: 8px;
  }

  .repository-heading strong,
  .repository-heading a {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .favorite {
    width: 1em;
    color: var(--warning-color, #f5b301);
  }

  .repository-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(130px, 100%), 1fr));
    gap: 8px;
    margin-top: 10px;
  }

  .repository.compact .repository-metrics {
    display: flex;
    overflow-x: auto;
    padding-bottom: 2px;
    scrollbar-width: thin;
  }

  .repository.compact .metric {
    flex: 1 0 120px;
    padding: 9px;
  }

  .repository.compact .metric .meta,
  .repository.compact .metric svg {
    display: none;
  }

  .repository.detail .repository-metrics {
    grid-template-columns: 1fr;
  }

  .badges {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    margin-top: 8px;
  }

  .badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    min-width: 0;
    padding: 3px 7px;
    border-radius: 999px;
    font-size: 0.7rem;
    color: var(--secondary-text-color);
    background: color-mix(in srgb, var(--divider-color) 50%, transparent);
  }

  .badge ha-icon {
    --mdc-icon-size: 14px;
  }

  .badge-label {
    font-weight: 650;
  }

  .diagnostics {
    margin-top: 12px;
    border-top: 1px solid var(--divider-color);
    padding-top: 12px;
  }

  .diagnostics pre {
    max-height: 260px;
    overflow: auto;
    padding: 10px;
    border-radius: 8px;
    color: var(--primary-text-color);
    background: color-mix(in srgb, var(--divider-color) 35%, transparent);
    font: 0.75rem/1.45 ui-monospace, SFMono-Regular, Consolas, monospace;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
  }

  .heatmap {
    display: grid;
    grid-template-columns: repeat(13, 1fr);
    gap: 3px;
    margin-top: 12px;
  }

  .heatmap span {
    aspect-ratio: 1;
    min-width: 5px;
    border-radius: 2px;
    background: color-mix(
      in srgb,
      var(--primary-color) calc(var(--intensity) * 22%),
      var(--divider-color)
    );
  }

  button,
  a {
    min-height: 40px;
    min-width: 40px;
  }

  button {
    border: 0;
    border-radius: 999px;
    padding: 0 14px;
    color: var(--primary-text-color);
    background: var(--gi-soft);
    cursor: pointer;
  }

  button:focus-visible,
  a:focus-visible,
  ha-card:focus-visible,
  pre:focus-visible {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  @media (max-width: 520px) {
    .card {
      padding: 12px;
    }

    .grid,
    :host([layout="compact"]) .grid,
    .repository-metrics {
      grid-template-columns: 1fr 1fr;
    }
  }

  @media (max-width: 360px) {
    .grid,
    :host([layout="compact"]) .grid {
      grid-template-columns: 1fr;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      scroll-behavior: auto !important;
      transition-duration: 0.001ms !important;
      animation-duration: 0.001ms !important;
      animation-iteration-count: 1 !important;
    }
  }
`;

function normalizeConfig(value, definition) {
    if (!value || typeof value !== "object") {
        throw new Error("GitHub Insights card configuration is required.");
    }
    if (value.type && value.type !== `custom:${definition.tag}`) {
        throw new Error(`Expected type custom:${definition.tag}.`);
    }
    const preset = definition.kind === "insights"
        ? PRESET_CONFIGS[value.preset ?? "dashboard"]
        : undefined;
    return {
        type: `custom:${definition.tag}`,
        preset: definition.kind === "insights"
            ? value.preset ?? "dashboard"
            : undefined,
        title: value.title,
        account: value.account,
        entity: value.entity,
        entities: { ...(value.entities ?? {}) },
        repositories: value.repositories ?? "auto",
        repository: value.repository,
        search: value.search,
        group_by: value.group_by ?? "none",
        favorites: [...(value.favorites ?? [])],
        repository_overrides: Object.fromEntries(Object.entries(value.repository_overrides ?? {}).map(([repository, override]) => [
            repository,
            {
                title: override.title,
                view: override.view,
                favorite: override.favorite,
                metrics: override.metrics ? [...override.metrics] : undefined,
                metric_badges: override.metric_badges?.map((badge) => ({
                    attribute: badge.attribute,
                    icon: badge.icon,
                    label: badge.label,
                })),
            },
        ])),
        include: {
            names: [...(value.include?.names ?? [])],
            visibility: [...(value.include?.visibility ?? [])],
        },
        exclude: {
            names: [...(value.exclude?.names ?? [])],
            archived: value.exclude?.archived ?? !value.show_archived,
            forked: value.exclude?.forked ?? value.show_forks === false,
        },
        sort: (value.sort ?? [
            { field: "workflow_health", direction: "ascending", nulls: "last" },
            { field: "last_push", direction: "descending", nulls: "last" },
            { field: "name", direction: "ascending", nulls: "last" },
        ]).map((sort) => ({ ...sort })),
        sections: [
            ...(value.sections ?? preset?.sections ?? definition.defaultSections),
        ],
        metrics: [
            ...(value.metrics ??
                (value.primary_metric || value.secondary_metric
                    ? [value.primary_metric, value.secondary_metric].filter((metric) => Boolean(metric))
                    : preset?.metrics ?? definition.defaultMetrics)),
        ],
        layout: value.layout ?? preset?.layout ?? definition.defaultLayout,
        view: value.view ?? "compact",
        period: value.period ?? "current_billing_cycle",
        show_forecast: value.show_forecast ?? true,
        show_archived: value.show_archived ?? false,
        show_forks: value.show_forks ?? true,
        show_estimated_minutes: value.show_estimated_minutes ?? true,
        show_metric_badges: value.show_metric_badges ?? true,
        show_debug: value.show_debug ?? false,
        metric_badges: (value.metric_badges ?? []).map((badge) => ({
            attribute: badge.attribute,
            icon: badge.icon,
            label: badge.label,
        })),
        reference_runner: value.reference_runner ?? "linux_standard",
        primary_metric: value.primary_metric ?? definition.defaultMetrics[0],
        secondary_metric: value.secondary_metric ?? definition.defaultMetrics[1],
        icon: value.icon ?? definition.icon,
        severity: {
            green: value.severity?.green ?? 0,
            amber: value.severity?.amber ?? 70,
            red: value.severity?.red ?? 90,
        },
        tap_action: value.tap_action,
        hold_action: value.hold_action,
        double_tap_action: value.double_tap_action,
    };
}
function stubConfig(definition) {
    return normalizeConfig({ type: `custom:${definition.tag}` }, definition);
}

const UNKNOWN_STATES = new Set(["unknown", "unavailable", "none", "null", ""]);
function entityAvailable(entity) {
    return Boolean(entity && !UNKNOWN_STATES.has(entity.state.toLowerCase()));
}
function numericState(entity) {
    if (!entityAvailable(entity))
        return undefined;
    const value = Number(entity?.state);
    return Number.isFinite(value) ? value : undefined;
}
function formatMetric(hass, entity, definition) {
    if (!entityAvailable(entity))
        return "Unavailable";
    const locale = hass?.locale?.language ?? hass?.language ?? "en";
    const value = entity?.state ?? "";
    const numberValue = Number(value);
    const unit = String(entity?.attributes.unit_of_measurement ?? "");
    if (definition.format === "boolean") {
        return value === "on" || value === "true" ? "Yes" : "No";
    }
    if (definition.format === "datetime") {
        const date = new Date(value);
        return Number.isNaN(date.valueOf())
            ? value
            : new Intl.DateTimeFormat(locale, {
                dateStyle: "medium",
                timeStyle: "short",
            }).format(date);
    }
    if (Number.isFinite(numberValue)) {
        if (definition.format === "currency") {
            const currency = String(entity?.attributes.currency ?? unit ?? "USD");
            try {
                return new Intl.NumberFormat(locale, {
                    style: "currency",
                    currency,
                    maximumFractionDigits: 2,
                }).format(numberValue);
            }
            catch {
                return `${numberValue.toLocaleString(locale)} ${currency}`.trim();
            }
        }
        const formatted = new Intl.NumberFormat(locale, {
            maximumFractionDigits: 2,
        }).format(numberValue);
        if (definition.format === "percent")
            return `${formatted}%`;
        return `${formatted}${unit ? ` ${unit}` : ""}`;
    }
    return value;
}
function safeHttpUrl(value) {
    if (typeof value !== "string")
        return undefined;
    try {
        const parsed = new URL(value);
        return parsed.protocol === "https:" || parsed.protocol === "http:"
            ? parsed.href
            : undefined;
    }
    catch {
        return undefined;
    }
}
function safeHttpsUrl(value) {
    const url = safeHttpUrl(value);
    return url?.startsWith("https:") ? url : undefined;
}
function safeText(value, maximumLength = 160) {
    if (typeof value !== "string" &&
        typeof value !== "number" &&
        typeof value !== "boolean") {
        return undefined;
    }
    const text = Array.from(String(value), (character) => {
        const code = character.charCodeAt(0);
        return code <= 31 || code === 127 ? " " : character;
    })
        .join("")
        .trim();
    return text ? text.slice(0, maximumLength) : undefined;
}
function severityClass(value, severity) {
    if (value === undefined)
        return "neutral";
    if (value >= (severity?.red ?? 90))
        return "critical";
    if (value >= (severity?.amber ?? 70))
        return "warning";
    return "healthy";
}

const UNAVAILABLE_STATES = new Set(["unknown", "unavailable", "none", "null", ""]);
function comparable(value) {
    if (typeof value === "number")
        return Number.isFinite(value) ? value : undefined;
    if (typeof value !== "string" || !value.trim())
        return undefined;
    if (UNAVAILABLE_STATES.has(value.trim().toLocaleLowerCase()))
        return undefined;
    const numeric = Number(value);
    if (Number.isFinite(numeric))
        return numeric;
    const timestamp = Date.parse(value);
    return Number.isNaN(timestamp) ? value.toLocaleLowerCase() : timestamp;
}
function compareValues(left, right, direction, nulls) {
    const a = comparable(left);
    const b = comparable(right);
    if (a === undefined || b === undefined) {
        if (a === b)
            return 0;
        return (a === undefined ? 1 : -1) * (nulls === "last" ? 1 : -1);
    }
    const result = typeof a === "number" && typeof b === "number"
        ? a - b
        : String(a).localeCompare(String(b));
    return direction === "descending" ? -result : result;
}
function sortValue(repository, field) {
    if (field === "name")
        return repository.name;
    if (field === "favorite")
        return repository.favorite ? 1 : 0;
    const entity = repository.entities.get(field);
    return entity?.state ?? entity?.attributes[field];
}
function repositoryAttribute(entities, attribute) {
    for (const entity of entities.values()) {
        if (attribute in entity.attributes)
            return entity.attributes[attribute];
    }
    return undefined;
}
function buildRepositories(discovered, hass, config) {
    const selected = config.repositories === "auto" ? undefined : new Set(config.repositories ?? []);
    const included = new Set(config.include?.names ?? []);
    const includedVisibility = new Set(config.include?.visibility ?? []);
    const excluded = new Set(config.exclude?.names ?? []);
    const favorites = new Set(config.favorites ?? []);
    const search = config.search?.trim().toLocaleLowerCase();
    const grouped = new Map();
    for (const reference of discovered) {
        if (!reference.repository)
            continue;
        if (selected && !selected.has(reference.repository))
            continue;
        const entity = hass?.states[reference.entityId];
        if (!entity)
            continue;
        const entities = grouped.get(reference.repository) ?? new Map();
        entities.set(reference.key, entity);
        grouped.set(reference.repository, entities);
    }
    const repositories = [...grouped.entries()]
        .filter(([name]) => !search || name.toLocaleLowerCase().includes(search))
        .filter(([name]) => included.size === 0 || included.has(name))
        .filter(([name]) => !excluded.has(name))
        .filter(([, entities]) => {
        const visibility = repositoryAttribute(entities, "visibility");
        return (includedVisibility.size === 0 ||
            (typeof visibility === "string" && includedVisibility.has(visibility)));
    })
        .filter(([, entities]) => {
        const archived = repositoryAttribute(entities, "archived") === true;
        return !(config.exclude?.archived ?? !config.show_archived) || !archived;
    })
        .filter(([, entities]) => {
        const fork = repositoryAttribute(entities, "fork") === true;
        return !(config.exclude?.forked ?? config.show_forks === false) || !fork;
    })
        .map(([name, entities]) => {
        const override = config.repository_overrides?.[name];
        return {
            name,
            title: override?.title ?? name,
            favorite: override?.favorite ?? favorites.has(name),
            entities,
            override,
        };
    });
    const sorts = config.sort ?? [];
    return repositories.sort((a, b) => {
        const favoriteDifference = Number(b.favorite) - Number(a.favorite);
        if (favoriteDifference)
            return favoriteDifference;
        for (const sort of sorts) {
            const difference = compareValues(sortValue(a, sort.field), sortValue(b, sort.field), sort.direction ?? "ascending", sort.nulls ?? "last");
            if (difference)
                return difference;
        }
        return a.name.localeCompare(b.name);
    });
}

class GitHubInsightsCard extends i {
    constructor() {
        super(...arguments);
        this.discovered = [];
        this.discoveryComplete = false;
        this.debugExpanded = false;
        this.copyStatus = "";
        this.discoveryGeneration = 0;
        this.lastTap = 0;
    }
    static { this.styles = cardStyles; }
    static { this.properties = {
        hass: { attribute: false },
        config: { attribute: false },
        discovered: { attribute: false, state: true },
        discoveryError: { attribute: false, state: true },
        discoveryComplete: { attribute: false, state: true },
        debugExpanded: { attribute: false, state: true },
        copyStatus: { attribute: false, state: true },
    }; }
    setConfig(config) {
        this.config = normalizeConfig(config, this.definition);
        this.setAttribute("layout", this.config.layout ?? "responsive");
        void this.refreshDiscovery();
    }
    static getStubConfig() {
        throw new Error("Card registration must provide getStubConfig.");
    }
    static getConfigElement() {
        throw new Error("Card registration must provide getConfigElement.");
    }
    getCardSize() {
        const count = this.config?.metrics?.length ?? this.definition.defaultMetrics.length;
        return Math.max(2, Math.ceil(count / 2) + 1);
    }
    updated(changed) {
        if (changed.has("hass"))
            void this.refreshDiscovery();
    }
    async refreshDiscovery() {
        if (!this.hass || !this.config)
            return;
        const generation = ++this.discoveryGeneration;
        this.discoveryComplete = false;
        try {
            const discovered = await EntityDiscoveryService.discover(this.hass, this.config);
            if (generation === this.discoveryGeneration) {
                this.discovered = discovered;
                this.discoveryError = undefined;
                this.discoveryComplete = true;
            }
        }
        catch (error) {
            if (generation === this.discoveryGeneration) {
                this.discovered = [];
                this.discoveryError =
                    error instanceof Error ? error.message : "Entity discovery failed.";
                this.discoveryComplete = true;
            }
        }
    }
    resolveEntity(key) {
        const candidates = this.config?.repository
            ? this.discovered.filter((entity) => entity.repository === this.config?.repository)
            : this.discovered;
        const reference = entitiesByKey(candidates).get(key);
        return reference ? this.hass?.states[reference.entityId] : undefined;
    }
    sparklineTemplate(entity, label) {
        const raw = entity?.attributes.trend;
        const values = Array.isArray(raw)
            ? raw.filter((value) => typeof value === "number")
            : [];
        if (values.length < 2)
            return A;
        const minimum = Math.min(...values);
        const maximum = Math.max(...values);
        const range = Math.max(maximum - minimum, 1);
        const points = values
            .map((value, index) => {
            const x = (index / (values.length - 1)) * 100;
            const y = 30 - ((value - minimum) / range) * 28;
            return `${x},${y}`;
        })
            .join(" ");
        return b `
      <svg viewBox="0 0 100 32" role="img" aria-label="${label} trend">
        <title>${label} trend from ${minimum} to ${maximum}</title>
        <polyline
          points=${points}
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          vector-effect="non-scaling-stroke"
        ></polyline>
      </svg>
    `;
    }
    metricLink(key, entity) {
        const attributes = entity?.attributes ?? {};
        const candidates = key.includes("workflow") || key.startsWith("actions_")
            ? [attributes.actions_url, attributes.workflow_url, attributes.html_url]
            : key.includes("issue")
                ? [attributes.issues_url, attributes.html_url]
                : key.includes("pull")
                    ? [attributes.pulls_url, attributes.html_url]
                    : key.includes("alert") || key.includes("scanning")
                        ? [attributes.security_url, attributes.html_url]
                        : [attributes.html_url, attributes.url];
        return candidates.map(safeHttpsUrl).find(Boolean);
    }
    badgeTemplate(entity, badges) {
        if (this.config?.show_metric_badges === false || badges.length === 0)
            return A;
        const rendered = badges.flatMap((badge) => {
            const value = safeText(entity?.attributes[badge.attribute], 60);
            if (!value)
                return [];
            const name = badge.label ?? badge.attribute.replaceAll("_", " ");
            return [b `
        <span class="badge" aria-label=${`${name}: ${value}`}>
          ${badge.icon
                    ? b `<ha-icon .icon=${badge.icon} aria-hidden="true"></ha-icon><span class="sr-only">${name}:</span>`
                    : b `<span class="badge-label">${name}:</span>`}
          ${value}
        </span>
      `];
        });
        return rendered.length ? b `<div class="badges">${rendered}</div>` : A;
    }
    metricTemplate(key, suppliedEntity, badges = this.config?.metric_badges ?? [], repositoryScoped = false) {
        const definition = metricDefinition(key);
        const entity = repositoryScoped ? suppliedEntity : suppliedEntity ?? this.resolveEntity(key);
        const available = entityAvailable(entity);
        const value = numericState(entity);
        const severity = definition.format === "percent"
            ? severityClass(value, this.config?.severity)
            : "neutral";
        const estimated = definition.estimated ? "Estimated · " : "";
        const source = safeText(entity?.attributes.source, 100) ?? definition.sourceLabel ?? "";
        const unavailableReason = String(entity?.attributes.availability_reason ?? "Metric is not exposed for the current permissions or capability.");
        return b `
      <article
        class="metric ${severity} ${available ? "" : "unavailable"} ${definition.prominent ? "prominent" : ""}"
        aria-label="${definition.label}: ${formatMetric(this.hass, entity, definition)}"
      >
        <div class="metric-heading">
          <ha-icon .icon=${definition.icon} aria-hidden="true"></ha-icon>
          ${this.metricLink(key, entity)
            ? b `<a
                class="metric-link"
                href=${this.metricLink(key, entity)}
                target="_blank"
                rel="noopener noreferrer"
                aria-label=${`${definition.label} on GitHub (opens in a new tab)`}
                @pointerdown=${(event) => event.stopPropagation()}
                @pointerup=${(event) => event.stopPropagation()}
              >${definition.label}</a>`
            : b `<span class="label">${definition.label}</span>`}
        </div>
        <strong class="value">${formatMetric(this.hass, entity, definition)}</strong>
        ${available
            ? estimated || source
                ? b `<span class="meta">${estimated}${source ? `Source: ${source}` : ""}</span>`
                : A
            : b `<span class="meta">${unavailableReason}</span>`}
        ${this.badgeTemplate(entity, badges)}
        ${definition.format === "percent" && value !== undefined
            ? b `<div
              class="bar"
              role="progressbar"
              aria-label=${definition.label}
              aria-valuemin="0"
              aria-valuemax="100"
              aria-valuenow=${Math.max(0, Math.min(100, value))}
              aria-valuetext=${`${formatMetric(this.hass, entity, definition)} used`}
            ><span style=${`--progress:${Math.max(0, Math.min(100, value))}%`}></span></div>`
            : A}
        ${this.sparklineTemplate(entity, definition.label)}
      </article>
    `;
    }
    repositoryUrl(repository) {
        for (const entity of repository.entities.values()) {
            const url = safeHttpsUrl(entity.attributes.repository_url);
            if (url)
                return url;
        }
        return undefined;
    }
    repositoryTemplate() {
        if (!this.config)
            return A;
        let repositories = buildRepositories(this.discovered, this.hass, this.config);
        if (this.config.repository) {
            repositories = repositories.filter((repository) => repository.name === this.config?.repository);
        }
        if (repositories.length === 0)
            return A;
        return b `
      <section class="repositories" aria-label="Discovered repositories">
        ${repositories.map((repository) => {
            const view = repository.override?.view ??
                (this.config?.layout === "detail"
                    ? "detail"
                    : this.config?.layout === "expanded"
                        ? "expanded"
                        : this.config?.layout === "compact"
                            ? "compact"
                            : this.config?.view ?? "compact");
            const metrics = repository.override?.metrics ?? this.config?.metrics ?? this.definition.defaultMetrics;
            const configuredBadges = repository.override?.metric_badges ?? this.config?.metric_badges;
            const badges = configuredBadges?.length
                ? configuredBadges
                : [
                    { attribute: "visibility", icon: "mdi:eye-outline" },
                    { attribute: "default_branch", label: "Branch" },
                ];
            const url = this.repositoryUrl(repository);
            return b `
            <article class="repository ${view}">
              <div class="repository-heading">
                <span class="favorite" aria-label=${repository.favorite ? "Favorite repository" : "Repository"}>
                  ${repository.favorite ? "★" : ""}
                </span>
                ${url
                ? b `<a
                      href=${url}
                      target="_blank"
                      rel="noopener noreferrer"
                      aria-label=${`${repository.title} on GitHub (opens in a new tab)`}
                      @pointerdown=${(event) => event.stopPropagation()}
                      @pointerup=${(event) => event.stopPropagation()}
                    >${repository.title}</a>`
                : b `<strong>${repository.title}</strong>`}
                <span class="meta">${this.config?.group_by === "organization"
                ? repository.name.split("/", 1)[0]
                : view === "detail"
                    ? "Detailed repository view"
                    : view === "expanded"
                        ? "Expanded repository details"
                        : "GitHub repository"}</span>
              </div>
              <div class="repository-metrics" aria-label=${`${repository.title} metrics`}>
                ${metrics.map((key) => this.metricTemplate(key, repository.entities.get(key), badges, true))}
              </div>
            </article>
          `;
        })}
      </section>
    `;
    }
    diagnosticsPayload() {
        if (!this.config)
            return "{}";
        const config = {
            type: this.config.type,
            layout: this.config.layout,
            view: this.config.view,
            metrics: this.config.metrics,
            sort: this.config.sort,
            repository_selection_count: Array.isArray(this.config.repositories)
                ? this.config.repositories.length
                : this.config.repositories,
            favorite_count: this.config.favorites?.length ?? 0,
            include_name_count: this.config.include?.names?.length ?? 0,
            include_visibility: this.config.include?.visibility,
            exclude_name_count: this.config.exclude?.names?.length ?? 0,
            exclude_archived: this.config.exclude?.archived,
            exclude_forked: this.config.exclude?.forked,
            repository_override_count: Object.keys(this.config.repository_overrides ?? {}).length,
            show_metric_badges: this.config.show_metric_badges,
            metric_badges: this.config.metric_badges,
        };
        const repositoryAliases = new Map();
        const entityAliases = new Map();
        const alias = (values, value, prefix) => {
            const current = values.get(value);
            if (current)
                return current;
            const created = `${prefix}_${values.size + 1}`;
            values.set(value, created);
            return created;
        };
        const entities = this.discovered
            .map(({ key, entityId, repository }) => ({
            key,
            entity: alias(entityAliases, entityId, "entity"),
            repository: repository
                ? alias(repositoryAliases, repository, "repository")
                : undefined,
        }))
            .sort((a, b) => `${a.repository ?? ""}:${a.key}:${a.entity}`.localeCompare(`${b.repository ?? ""}:${b.key}:${b.entity}`));
        return JSON.stringify({ config, entities }, null, 2);
    }
    diagnosticsTemplate() {
        if (!this.config?.show_debug)
            return A;
        const panelId = `${this.definition.tag}-diagnostics`;
        return b `
      <section class="diagnostics">
        <button
          type="button"
          aria-expanded=${String(this.debugExpanded)}
          aria-controls=${panelId}
          @click=${(event) => {
            event.stopPropagation();
            this.debugExpanded = !this.debugExpanded;
        }}
        >
          ${this.debugExpanded ? "Hide" : "Show"} diagnostics
        </button>
        ${this.debugExpanded
            ? b `<div id=${panelId}>
              <p class="meta">Sanitized resolved configuration and discovered entity mapping.</p>
              <pre tabindex="0">${this.diagnosticsPayload()}</pre>
              <button
                type="button"
                aria-label="Copy sanitized diagnostics to clipboard"
                @click=${async (event) => {
                event.stopPropagation();
                try {
                    await navigator.clipboard.writeText(this.diagnosticsPayload());
                    this.copyStatus = "Diagnostics copied.";
                }
                catch {
                    this.copyStatus = "Unable to copy diagnostics.";
                }
            }}
              >Copy diagnostics</button>
              <span class="sr-only" role="status" aria-live="polite">${this.copyStatus}</span>
            </div>`
            : A}
      </section>
    `;
    }
    heatmapTemplate() {
        if (this.definition.kind !== "insights" ||
            !this.config?.sections?.includes("contributions")) {
            return A;
        }
        const entity = this.resolveEntity("contributions");
        const raw = entity?.attributes.calendar;
        const values = Array.isArray(raw)
            ? raw.filter((value) => typeof value === "number").slice(-91)
            : [];
        if (values.length === 0)
            return A;
        const maximum = Math.max(...values, 1);
        return b `
      <div class="heatmap" role="img" aria-label="Contribution activity heatmap">
        ${values.map((value) => b `<span
              title=${`${value} contributions`}
              style=${`--intensity:${Math.ceil((value / maximum) * 4)}`}
            ></span>`)}
      </div>
    `;
    }
    statusTemplate() {
        if (this.discoveryError) {
            return b `<div class="status error" role="alert">
        <ha-icon icon="mdi:alert-circle-outline"></ha-icon>
        <span>${this.discoveryError}</span>
      </div>`;
        }
        const blocked = this.resolveEntity("actions_blocked");
        if (blocked?.state === "on") {
            return b `<div class="status blocked" role="alert">
        <ha-icon icon="mdi:block-helper"></ha-icon>
        <span><strong>Actions blocked.</strong> GitHub enforcement is preventing applicable usage.</span>
      </div>`;
        }
        const warning = this.resolveEntity("actions_budget_warning");
        if (warning?.state === "on") {
            return b `<div class="status warning" role="status">
        <ha-icon icon="mdi:alert-outline"></ha-icon>
        <span>GitHub Actions budget warning threshold reached.</span>
      </div>`;
        }
        const partial = this.discovered
            .map((entry) => this.hass?.states[entry.entityId])
            .find((entity) => entity?.attributes.error);
        if (partial) {
            return b `<div class="status warning" role="status">
        <ha-icon icon="mdi:cloud-alert-outline"></ha-icon>
        <span>Some GitHub data is stale or unavailable: ${String(partial.attributes.error)}</span>
      </div>`;
        }
        return A;
    }
    sectionForMetric(key) {
        if (["contributions", "current_streak", "longest_streak"].includes(key)) {
            return "contributions";
        }
        const group = metricDefinition(key).group;
        if (group === "billing")
            return "usage";
        if (group === "actions")
            return "actions";
        if (group === "copilot")
            return "copilot";
        if (group === "activity")
            return "activity";
        if (group === "security")
            return "security";
        return "overview";
    }
    metricSectionsTemplate(metrics) {
        const sections = this.config?.sections ?? this.definition.defaultSections;
        return sections.map((section) => {
            const sectionMetrics = metrics.filter((key) => this.sectionForMetric(key) === section);
            if (sectionMetrics.length === 0)
                return A;
            return b `
        <section class="metric-section" aria-labelledby=${`${this.definition.tag}-${section}`}>
          <h3 id=${`${this.definition.tag}-${section}`}>
            ${section.replace(/^\w/, (value) => value.toUpperCase())}
          </h3>
          <div class="grid">
            ${sectionMetrics.map((key) => this.metricTemplate(key))}
          </div>
        </section>
      `;
        });
    }
    actionFor(event) {
        if (event.type === "contextmenu")
            return this.config?.hold_action;
        return this.config?.tap_action;
    }
    async runAction(action) {
        if (!action || action.action === "none")
            return;
        if (action.action === "navigate" && action.navigation_path) {
            history.pushState(null, "", action.navigation_path);
            window.dispatchEvent(new Event("location-changed"));
            return;
        }
        if (action.action === "url") {
            const url = safeHttpUrl(action.url_path);
            if (url)
                window.open(url, "_blank", "noopener,noreferrer");
            return;
        }
        if (action.action === "call-service" && action.service && this.hass?.callService) {
            const [domain, service] = action.service.split(".", 2);
            if (domain && service) {
                await this.hass.callService(domain, service, action.service_data);
            }
            return;
        }
        const entityId = action.entity ?? this.config?.entity;
        if (entityId) {
            this.dispatchEvent(new CustomEvent("hass-more-info", {
                bubbles: true,
                composed: true,
                detail: { entityId },
            }));
        }
    }
    handlePointerDown(event) {
        if (event.composedPath()[0]?.closest?.("a,button"))
            return;
        if (!this.config?.hold_action)
            return;
        this.holdTimer = window.setTimeout(() => {
            void this.runAction(this.config?.hold_action);
            this.holdTimer = undefined;
        }, 500);
    }
    handlePointerUp(event) {
        if (event.composedPath()[0]?.closest?.("a,button"))
            return;
        if (this.holdTimer === undefined && this.config?.hold_action)
            return;
        if (this.holdTimer !== undefined) {
            window.clearTimeout(this.holdTimer);
            this.holdTimer = undefined;
        }
        const now = Date.now();
        if (now - this.lastTap < 300 && this.config?.double_tap_action) {
            this.lastTap = 0;
            void this.runAction(this.config.double_tap_action);
        }
        else {
            this.lastTap = now;
            void this.runAction(this.actionFor(event));
        }
    }
    eventTargetsInteractive(event) {
        return event
            .composedPath()
            .some((target) => target instanceof Element && target.matches("a,button"));
    }
    render() {
        if (!this.config)
            return A;
        const metrics = (this.config.metrics ?? this.definition.defaultMetrics).filter((key) => this.config?.show_estimated_minutes !== false ||
            !metricDefinition(key).estimated);
        const visibleMetrics = this.definition.kind === "insights"
            ? metrics.filter((key) => this.config?.sections?.includes(this.sectionForMetric(key)))
            : metrics;
        const anyConfigured = visibleMetrics.some((key) => this.resolveEntity(key));
        const isRepositoryCard = this.definition.kind === "repository";
        const hasRepositories = isRepositoryCard &&
            buildRepositories(this.discovered, this.hass, this.config).some((repository) => !this.config?.repository ||
                repository.name === this.config.repository);
        const account = this.resolveEntity("account");
        const avatarUrl = safeHttpsUrl(account?.attributes.avatar_url);
        const isLoading = Boolean(this.hass?.connection) &&
            !this.discoveryComplete &&
            !this.discoveryError;
        return b `
      <ha-card
        tabindex="0"
        role="group"
        aria-label=${this.config.title ?? this.definition.name}
        @pointerdown=${this.handlePointerDown}
        @pointerup=${this.handlePointerUp}
        @keydown=${(event) => {
            if (event.target === event.currentTarget && (event.key === "Enter" || event.key === " ")) {
                event.preventDefault();
                void this.runAction(this.config?.tap_action);
            }
        }}
        @contextmenu=${(event) => {
            if (this.eventTargetsInteractive(event))
                return;
            event.preventDefault();
            void this.runAction(this.config?.hold_action);
        }}
      >
        <section class="card">
          <header class="header">
            <div class="account">
              ${avatarUrl
            ? b `<img
                    src=${avatarUrl}
                    alt=""
                    width="40"
                    height="40"
                    loading="lazy"
                    referrerpolicy="no-referrer"
                  />`
            : A}
              <div>
              <h2>${this.config.title ?? this.definition.name}</h2>
              <div class="subtitle">${this.definition.description}</div>
              </div>
            </div>
            <ha-icon .icon=${this.config.icon ?? this.definition.icon} aria-hidden="true"></ha-icon>
          </header>
          ${this.statusTemplate()}
          ${isLoading
            ? b `<div class="status" role="status">Discovering GitHub Insights entities…</div>`
            : A}
          ${!isLoading && !anyConfigured && !hasRepositories && !this.discoveryError
            ? b `<div class="status empty" role="status">
                No supported metrics are available. Enable the relevant GitHub capability or select entities in the card editor.
              </div>`
            : isRepositoryCard
                ? A
                : this.metricSectionsTemplate(visibleMetrics)}
          ${this.repositoryTemplate()} ${this.heatmapTemplate()} ${this.diagnosticsTemplate()}
        </section>
      </ha-card>
    `;
    }
}
function createCardClass(definition) {
    return class extends GitHubInsightsCard {
        constructor() {
            super(...arguments);
            this.definition = definition;
        }
        static getStubConfig() {
            return stubConfig(definition);
        }
        static getConfigElement() {
            return document.createElement(definition.editorTag);
        }
    };
}

class GitHubInsightsEditor extends i {
    constructor() {
        super(...arguments);
        this.overrideError = "";
    }
    static { this.properties = {
        hass: { attribute: false },
        config: { attribute: false },
        overrideError: { attribute: false, state: true },
    }; }
    static { this.styles = i$3 `
    :host {
      display: grid;
      gap: 16px;
      padding: 8px 0;
      color: var(--primary-text-color);
    }
    label,
    fieldset {
      display: grid;
      gap: 6px;
    }
    fieldset {
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-card-border-radius, 12px);
      padding: 12px;
    }
    input,
    select,
    textarea {
      min-height: 42px;
      padding: 0 10px;
      color: var(--primary-text-color);
      background: var(--card-background-color);
      border: 1px solid var(--divider-color);
      border-radius: 8px;
    }
    textarea {
      min-height: 110px;
      padding-block: 8px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
    }
    input:focus-visible,
    select:focus-visible,
    textarea:focus-visible,
    button:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 2px;
    }
    .options {
      display: grid;
      gap: 6px;
    }
    .ordered {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto auto;
      align-items: center;
      gap: 6px;
      min-height: 38px;
    }
    .check {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 36px;
    }
    button {
      min-width: 36px;
      min-height: 36px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      color: var(--primary-text-color);
      background: var(--secondary-background-color);
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.45;
      cursor: default;
    }
    .error {
      color: var(--error-color);
    }
  `; }
    setConfig(config) {
        this.config = normalizeConfig(config, this.definition);
    }
    updateConfig(patch) {
        if (!this.config)
            return;
        this.config = normalizeConfig({ ...this.config, ...patch }, this.definition);
        this.dispatchEvent(new CustomEvent("config-changed", {
            bubbles: true,
            composed: true,
            detail: { config: this.config },
        }));
    }
    moveItem(values, index, offset) {
        const target = index + offset;
        if (target < 0 || target >= values.length)
            return values;
        const reordered = [...values];
        [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
        return reordered;
    }
    toggleMetric(key, checked) {
        const metrics = [...(this.config?.metrics ?? [])];
        const index = metrics.indexOf(key);
        if (checked && index === -1)
            metrics.push(key);
        if (!checked && index !== -1)
            metrics.splice(index, 1);
        this.updateConfig({ metrics });
    }
    toggleSection(section, checked) {
        const sections = [...(this.config?.sections ?? [])];
        const index = sections.indexOf(section);
        if (checked && index === -1)
            sections.push(section);
        if (!checked && index !== -1)
            sections.splice(index, 1);
        this.updateConfig({ sections });
    }
    orderedToggle(label, checked, index, length, toggle, move) {
        return b `
      <div class="ordered">
        <label class="check">
          <input
            type="checkbox"
            .checked=${checked}
            @change=${(event) => toggle(event.target.checked)}
          />
          ${label}
        </label>
        <button
          type="button"
          aria-label=${`Move ${label} up`}
          ?disabled=${!checked || index <= 0}
          @click=${() => move(-1)}
        >↑</button>
        <button
          type="button"
          aria-label=${`Move ${label} down`}
          ?disabled=${!checked || index < 0 || index >= length - 1}
          @click=${() => move(1)}
        >↓</button>
      </div>
    `;
    }
    insightsOptions() {
        if (!this.config || this.definition.kind !== "insights")
            return A;
        const sections = this.config.sections ?? [];
        const orderedSections = [
            ...sections,
            ...INSIGHTS_SECTIONS.filter((section) => !sections.includes(section)),
        ];
        return b `
      <label>
        Preset
        <select
          aria-label="Card preset"
          .value=${this.config.preset ?? "dashboard"}
          @change=${(event) => {
            const preset = event.target
                .value;
            const defaults = PRESET_CONFIGS[preset];
            this.updateConfig({
                preset,
                metrics: [...defaults.metrics],
                sections: [...defaults.sections],
                layout: defaults.layout,
            });
        }}
        >
          ${Object.keys(PRESET_CONFIGS).map((preset) => b `<option value=${preset}>${preset.replaceAll("_", " ")}</option>`)}
        </select>
      </label>
      <fieldset>
        <legend>Sections and order</legend>
        <div class="options">
          ${orderedSections.map((section) => {
            const index = sections.indexOf(section);
            return this.orderedToggle(section, index !== -1, index, sections.length, (checked) => this.toggleSection(section, checked), (offset) => this.updateConfig({
                sections: this.moveItem(sections, index, offset),
            }));
        })}
        </div>
      </fieldset>
    `;
    }
    repositoryOptions() {
        if (!this.config || this.definition.kind !== "repository")
            return A;
        const selectionMode = this.config.repository
            ? "single"
            : Array.isArray(this.config.repositories)
                ? "multiple"
                : "auto";
        return b `
      <label>
        Repository selection
        <select
          aria-label="Repository selection"
          .value=${selectionMode}
          @change=${(event) => {
            const mode = event.target.value;
            this.updateConfig(mode === "single"
                ? { repository: "", repositories: "auto" }
                : mode === "multiple"
                    ? { repository: undefined, repositories: [] }
                    : { repository: undefined, repositories: "auto" });
        }}
        >
          <option value="auto">Auto-discovered collection</option>
          <option value="multiple">Selected repositories</option>
          <option value="single">One repository</option>
        </select>
      </label>
      ${selectionMode === "single"
            ? b `<label>
            Repository
            <input
              aria-label="Repository full name"
              placeholder="owner/repository"
              .value=${this.config.repository ?? ""}
              @input=${(event) => this.updateConfig({
                repository: event.target.value || undefined,
            })}
            />
          </label>`
            : A}
      ${selectionMode === "multiple"
            ? b `<label>
            Repositories
            <input
              aria-label="Selected repositories"
              placeholder="owner/one, owner/two"
              .value=${Array.isArray(this.config.repositories)
                ? this.config.repositories.join(", ")
                : ""}
              @change=${(event) => this.updateConfig({
                repositories: event.target.value
                    .split(",")
                    .map((value) => value.trim())
                    .filter(Boolean),
            })}
            />
          </label>`
            : A}
      <label>
        Search repositories
        <input
          aria-label="Search repositories"
          .value=${this.config.search ?? ""}
          @input=${(event) => this.updateConfig({
            search: event.target.value || undefined,
        })}
        />
      </label>
      <label>
        Favorite repositories
        <input
          aria-label="Favorite repositories"
          placeholder="owner/one, owner/two"
          .value=${(this.config.favorites ?? []).join(", ")}
          @change=${(event) => this.updateConfig({
            favorites: event.target.value
                .split(",")
                .map((value) => value.trim())
                .filter(Boolean),
        })}
        />
      </label>
      <label>
        Primary repository sort
        <select
          aria-label="Primary repository sort"
          .value=${this.config.sort?.[0]?.field ?? "workflow_health"}
          @change=${(event) => {
            const field = event.target.value;
            this.updateConfig({
                sort: [
                    {
                        field,
                        direction: field === "last_push" || field === "stars"
                            ? "descending"
                            : "ascending",
                        nulls: "last",
                    },
                    { field: "name", direction: "ascending", nulls: "last" },
                ],
            });
        }}
        >
          ${["workflow_health", "last_push", "stars", "open_issues", "name"].map((field) => b `<option value=${field}>${field.replaceAll("_", " ")}</option>`)}
        </select>
      </label>
      <label>
        Repository overrides (JSON)
        <textarea
          aria-label="Repository overrides"
          .value=${JSON.stringify(this.config.repository_overrides ?? {}, null, 2)}
          @change=${(event) => {
            try {
                const value = JSON.parse(event.target.value || "{}");
                this.overrideError = "";
                this.updateConfig({ repository_overrides: value });
            }
            catch {
                this.overrideError = "Repository overrides must be valid JSON.";
            }
        }}
        ></textarea>
        ${this.overrideError
            ? b `<span class="error" role="alert">${this.overrideError}</span>`
            : A}
      </label>
    `;
    }
    render() {
        if (!this.config)
            return A;
        const metrics = this.config.metrics ?? [];
        const layouts = this.definition.kind === "repository"
            ? ["responsive", "compact", "expanded", "detail"]
            : ["responsive", "compact", "expanded"];
        const metricDefinitions = Object.values(METRICS);
        const orderedMetrics = [
            ...metrics
                .map((key) => METRICS[key])
                .filter((metric) => metric !== undefined),
            ...metricDefinitions.filter((metric) => !metrics.includes(metric.key)),
        ];
        return b `
      <label>
        Title
        <input
          aria-label="Card title"
          .value=${this.config.title ?? ""}
          @input=${(event) => this.updateConfig({
            title: event.target.value || undefined,
        })}
        />
      </label>
      ${this.insightsOptions()}
      <label>
        Presentation
        <select
          aria-label="Card presentation"
          .value=${this.config.layout ?? this.definition.defaultLayout}
          @change=${(event) => this.updateConfig({
            layout: event.target
                .value,
        })}
        >
          ${layouts.map((layout) => b `<option value=${layout}>${layout}</option>`)}
        </select>
      </label>
      ${this.repositoryOptions()}
      <fieldset>
        <legend>Metrics and order</legend>
        <div class="options">
          ${orderedMetrics.map((metric) => {
            const index = metrics.indexOf(metric.key);
            return this.orderedToggle(`${metric.label}${metric.estimated ? " (estimated)" : ""}`, index !== -1, index, metrics.length, (checked) => this.toggleMetric(metric.key, checked), (offset) => this.updateConfig({
                metrics: this.moveItem(metrics, index, offset),
            }));
        })}
        </div>
      </fieldset>
      <fieldset>
        <legend>Display options</legend>
        ${this.checkbox("Show estimated equivalent minutes", this.config.show_estimated_minutes ?? true, (show_estimated_minutes) => this.updateConfig({ show_estimated_minutes }))}
        ${this.checkbox("Show forecast when supplied by GitHub Insights", this.config.show_forecast ?? true, (show_forecast) => this.updateConfig({ show_forecast }))}
        ${this.checkbox("Show metric attribute badges", this.config.show_metric_badges ?? true, (show_metric_badges) => this.updateConfig({ show_metric_badges }))}
        <label>
          Badge attributes
          <input
            aria-label="Metric badge attributes"
            placeholder="visibility, default_branch"
            .value=${(this.config.metric_badges ?? [])
            .map((badge) => badge.attribute)
            .join(", ")}
            @change=${(event) => this.updateConfig({
            metric_badges: event.target.value
                .split(",")
                .map((attribute) => attribute.trim())
                .filter(Boolean)
                .map((attribute) => ({ attribute })),
        })}
          />
        </label>
        ${this.checkbox("Show sanitized diagnostics panel", this.config.show_debug ?? false, (show_debug) => this.updateConfig({ show_debug }))}
      </fieldset>
    `;
    }
    checkbox(label, checked, update) {
        return b `<label class="check">
      <input
        type="checkbox"
        .checked=${checked}
        @change=${(event) => update(event.target.checked)}
      />
      ${label}
    </label>`;
    }
}
function createEditorClass(definition) {
    return class extends GitHubInsightsEditor {
        constructor() {
            super(...arguments);
            this.definition = definition;
        }
    };
}

const GITHUB_INSIGHTS_IMPLEMENTATION_PHASE = 9;
for (const definition of CARD_DEFINITIONS) {
    if (!customElements.get(definition.editorTag)) {
        customElements.define(definition.editorTag, createEditorClass(definition));
    }
    if (!customElements.get(definition.tag)) {
        customElements.define(definition.tag, createCardClass(definition));
    }
}
window.customCards = window.customCards ?? [];
for (const definition of CARD_DEFINITIONS) {
    if (!window.customCards.some((card) => card.type === definition.tag)) {
        window.customCards.push({
            type: definition.tag,
            name: definition.name,
            description: definition.description,
            preview: true,
        });
    }
}
console.info(`%c GitHub Insights Cards %c ${CARD_DEFINITIONS.length} cards registered `, "color:white;background:#24292f;padding:3px 6px;border-radius:4px 0 0 4px", "color:#24292f;background:#58a6ff;padding:3px 6px;border-radius:0 4px 4px 0");

export { CARD_DEFINITIONS, EntityDiscoveryService, GITHUB_INSIGHTS_IMPLEMENTATION_PHASE, METRICS, buildRepositories, entitiesByKey, entityAvailable, formatMetric, metricDefinition, normalizeConfig, numericState, safeHttpUrl, safeHttpsUrl, safeText, severityClass, stubConfig };
