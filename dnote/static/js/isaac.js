// Taken from https://github.com/rubycon/isaac.js
/* ----------------------------------------------------------------------
 * Copyright (c) 2012 Yves-Marie K. Rinquin
 *
 * Permission is hereby granted, free of charge, to any person obtaining
 * a copy of this software and associated documentation files (the
 * "Software"), to deal in the Software without restriction, including
 * without limitation the rights to use, copy, modify, merge, publish,
 * distribute, sublicense, and/or sell copies of the Software, and to
 * permit persons to whom the Software is furnished to do so, subject to
 * the following conditions:
 *
 * The above copyright notice and this permission notice shall be
 * included in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 * EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 * NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
 * LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
 * OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
 * WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 */
 String.prototype.toIntArray=function(){var e,t,n,r=[],i=[],s=0,o=this+"\0\0\0",u=o.length-1;while(s<u)e=o.charCodeAt(s++),t=o.charCodeAt(s+1),e<128?r.push(e):e<2048?(r.push(e>>>6&31|192),r.push(e>>>0&63|128)):(e&63488)!=55296?(r.push(e>>>12&15|224),r.push(e>>>6&63|128),r.push(e>>>0&63|128)):(e&64512)==55296&&(t&64512)==56320&&(n=(t&63|(e&63)<<10)+65536,r.push(n>>>18&7|240),r.push(n>>>12&63|128),r.push(n>>>6&63|128),r.push(n>>>0&63|128),s++),r.length>3&&i.push(r.shift()<<0|r.shift()<<8|r.shift()<<16|r.shift()<<24);return i};var isaac=function(){function o(e,t){var n=(e&65535)+(t&65535),r=(e>>>16)+(t>>>16)+(n>>>16);return r<<16|n&65535}function u(){t=n=r=0;for(var o=0;o<256;++o)e[o]=i[o]=0;s=0}function a(t){function g(){n^=r<<11,l=o(l,n),r=o(r,a),r^=a>>>2,c=o(c,r),a=o(a,l),a^=l<<8,h=o(h,a),l=o(l,c),l^=c>>>16,p=o(p,l),c=o(c,h),c^=h<<10,d=o(d,c),h=o(h,p),h^=p>>>4,n=o(n,h),p=o(p,d),p^=d<<8,r=o(r,p),d=o(d,n),d^=n>>>9,a=o(a,d),n=o(n,r)}var n,r,a,l,c,h,p,d,v;n=r=a=l=c=h=p=d=2654435769,t&&typeof t=="string"&&(t=t.toIntArray()),t&&typeof t=="number"&&(t=[t]);if(t instanceof Array){u();for(v=0;v<t.length;v++)i[v&255]+=typeof t[v]=="number"?t[v]:0}for(v=0;v<4;v++)g();for(v=0;v<256;v+=8)t&&(n=o(n,i[v+0]),r=o(r,i[v+1]),a=o(a,i[v+2]),l=o(l,i[v+3]),c=o(c,i[v+4]),h=o(h,i[v+5]),p=o(p,i[v+6]),d=o(d,i[v+7])),g(),e[v+0]=n,e[v+1]=r,e[v+2]=a,e[v+3]=l,e[v+4]=c,e[v+5]=h,e[v+6]=p,e[v+7]=d;if(t)for(v=0;v<256;v+=8)n=o(n,e[v+0]),r=o(r,e[v+1]),a=o(a,e[v+2]),l=o(l,e[v+3]),c=o(c,e[v+4]),h=o(h,e[v+5]),p=o(p,e[v+6]),d=o(d,e[v+7]),g(),e[v+0]=n,e[v+1]=r,e[v+2]=a,e[v+3]=l,e[v+4]=c,e[v+5]=h,e[v+6]=p,e[v+7]=d;f(),s=256}function f(s){var u,a,f;s=s&&typeof s=="number"?Math.abs(Math.floor(s)):1;while(s--){r=o(r,1),n=o(n,r);for(u=0;u<256;u++){switch(u&3){case 0:t^=t<<13;break;case 1:t^=t>>>6;break;case 2:t^=t<<2;break;case 3:t^=t>>>16}t=o(e[u+128&255],t),a=e[u],e[u]=f=o(e[a>>>2&255],o(t,n)),i[u]=n=o(e[f>>>10&255],a)}}}function l(){return s--||(f(),s=255),i[s]}function c(){return{a:t,b:n,c:r,m:e,r:i}}var e=Array(256),t=0,n=0,r=0,i=Array(256),s=0;return a(Math.random()*4294967295),{reset:u,seed:a,prng:f,rand:l,internals:c}}();isaac.random=function(){return.5+this.rand()*2.3283064365386963e-10};
