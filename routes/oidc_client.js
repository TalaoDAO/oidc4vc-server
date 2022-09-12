import { Issuer } from 'openid-client';

const altme = await Issuer.discover('http://192.168.0.220:3000/sandbox/op');
console.log('Discovered issuer %s %O', googleIssuer.issuer, googleIssuer.metadata);