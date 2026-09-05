# Hyphanet threat-model worksheet — Lab 7.6
# (the Lab 5.7 method, re-run a third time — now for a Hyphanet publisher)
#
# Score each column 1 (low) .. 5 (high).  weight = L x I x E.
# Fill this for a SPECIFIC activity - opennet vs darknet, a one-off insert vs a
# maintained freesite - not for "Hyphanet in general". The rows already reflect
# what vanishes, what is new, and what refuses to change; the weights are yours.

Mode (opennet / darknet): __________   Activity: ____________________________

threat                          L   I   E   weight   vs onion / eepsite
-----------------------------   -   -   -   ------   ---------------------------------
application leak in content     .   .   .   ......   unchanged - inserted content betrays you
operator OPSEC mistake          .   .   .   ......   unchanged - persona, reuse, stylometry
exit reads destination/content  .   .   .   ......   absent - there is no exit
service host located / seized   .   .   .   ......   absent - there is no host to seize
routing / correlation adversary .   .   .   ......   opennet risk; small in a trusted darknet
compromised / coerced friend    .   .   .   ......   NEW - the mesh is only as safe as its members
keyword (KSK) squat / poison    .   .   .   ......   NEW-ish - the purest naming chokepoint
content evicted (forgetful)     .   .   .   ......   NEW framing - availability, not exposure

# Headline: Hyphanet is not MORE anonymous than Tor or I2P - it optimizes a
# different thing (persistent, deniable, censorship-resistant publishing) and is
# poor at what Tor is built for. In darknet the top row is usually the friend you
# trusted wrongly - the strongest posture in the book moves the whole problem onto
# your judgment of people. And the app-leak / OPSEC rows still have not moved.
