# We don't have a separate INITEX, so we run this first every time.
SETUP = r"""
\immediate\catcode `{ = 1 \endlinechar=13
\catcode `} = 2
\catcode `$ = 3 {\catcode`$13\gdef\dol{$}}
\catcode `& = 4
\let\paR=\par
\let\%=\relax
\outer\xdef\par{\catcode `\% 14}
  % this line should change % from type 5 to type 14
\let\par=\paR \defaulthyphenchar=`- \defaultskewchar=256
\ifx\initex\undefined  \def\initex{} % next lines are skipped if format loaded
  \catcode `# = 6 \catcode `U=\catcode`# % # for parameters
  \catcode `^ = 7 \catcode `| = 8 % ^ for superscripts and | for subscripts
  \catcode `~ = 9 % ~ will be ignored
  \catcode `* = 10 % * will be like a space
  \catcode `E = 12 % E is not a letter
  \catcode`\@ = 15 % @ will be invalid
  \catcode `^^A = 0008 % this is another way to get a subscript
  \catcode `\^^@ = 11 % a strange letter will be allowed
  \catcode `\^^? = \badness % and so will a strange escape delimiter
  \fontdimen12\nullfont=13pt % give the null font more parameters
  \font\trip = trip\relax % see TRIP.PL for details of this font
  ^^?trip  \font\smalltrip=trip scaled 500 % this will be our symbols font
  \global\fontdimen22\smalltrip 7pt % the axis height
  \textfont2=\smalltrip \scriptfont2 \smalltrip \scriptscriptfont2 \smalltrip
  \nonstopmode\lccode256-0\mathchardef\a="8000\def\a{ SCALED 3~2769}
  \font\rip=trip\a % font \rip will be the same as \trip
  \skewchar\rip=`B \countdef\countz % \countz will be \count0
  \def\on{1} \toksdef\tokens=256 \show\errorstopmode
  \showthe\font \showthe\pageshrink \showthe\pagegoal
  \font\bigtr^^@p=trip at20pt\textfont3=\bigtr^^@p % this will be extension font
  \skip200 = 10pt plUs5fil\ifdim\hsize<\hsize\fi lllminus 0 fill
  \setbox200=\vbox{\hrule\vskip\skip200} \wd200-2pt \setbox100=\hbox{A}
  \skipdef\shkip100\shkip -18pt plus\catcode`\}fil minus 10fil
  \advance\shkip by \skip200 \dimen33=3pt \count33=-\dimen33
  \divide\shkip by \count33
  \multiply\shkip by \count33 % so \skip100=-6pt plus 3filll minus 9fil
  \count200 -5 \multiply\count200 by -100 % \count200 is 500
  \count100=1000000 \divide\count100 by \count200 % \count100 is 2000
  \dimen100=,00152587890625in % (100/65536)in = 7227sp
  \multiply\dimen100 by 65536 \divide\dimen100 by 9 % \dimen100 is 803pt
  \lineskip 0pt plus 40pt
  \baselineskip=10pt plus 41pt
  \parskip -0pt plus 42pt minus 8pt
  \splittopskip 1pt plus 43pt
  \splitmaxdepth -2pt \boxmaxdepth 1000pt
  \belowdisplayskip 3pt plus 44pt minus\baselineskip \abovedisplayskip3pt
  \abovedisplayshortskip 1pt plus 45pt minus\dimen100
  \belowdisplayshortskip -\count33sp plus 46pt
  \global\mathchardef\minus"232D % mathbin, family 3, character "2D (-)
  \thinmuskip 1mu plus 2fill minus 3mu
  \medmuskip 2mu minus 3mu
  \thickmuskip -4mu
  \def\gobble#1{} \floatingpenalty 100 \holdinginserts1
  \everypar{A\insert200{\baselineskip400pt\splittopskip\count15pt\hbox{\vadjust
        {\penalty999}}\hbox to -10pt{}}\showthe\pagetotal\showthe\pagegoal
    \advance\count15by1\mark{\the\count15}\splitmaxdepth-1pt
    \paR\gobble} % this aborts every paragraph abruptly
  \def\weird#1{\csname\expandafter\gobble\string#1 \string\csname\endcsname}
  \message{\the\output\weird\one on line \the\inputlineno}
  \hyphenpenalty 88 \exhyphenpenalty 89 \badness
  \clubpenalty 125 \widowpenalty 125 \displaywidowpenalty -125
  \brokenpenalty 37
  \interlinepenalty -125
  \doublehyphendemerits 1000
  \finalhyphendemerits 100000
  \mag 2000 \righthyphenmin=1000000000
  \delimiterfactor 10 \delimitershortfall 190pt
  \showboxbreadth 55 \showboxdepth 9999 \chardef\nul0\def\0{\nul}
  \tracingstats=4 \tracinglostchars=2 \tracingparagraphs\day \tracingpages\year
  \chardef\?=`b \lccode`A=1 \let\^^bbb \hyphenchar\trip=1
  \language-1\hyphenation\relax{b-\?-\char`b -\^^bb-^^62-^^" -t- }\lccode`149
  {\everypar{\parindent\\\looseness-1}\skipdef\\8\language\?\\.01014pt\patterns
  {0111}\emergencystretch9pt\language255\patterns{\the\\} % \patterns{.01015pt}
  {\language256\patterns{0111 \?50AA1b3 *1AcA. bb bb1 0B2B0 b1c}} % *==space
  \pretolerance-1\setbox0=\hbox{11}\setbox0=\hbox{\hbadness100\valign{#\cr
  \hskip-9pt7A\righthyphenmin0\setlanguage\?\unhbox0{*\language`b11\noboundary}
  1Z1pts\patterns{q9q} -\0qq \showlists{\language\?\noboundary111}%
  \hyphenchar\rip=`-\cr}}\patterns{toolate}\showbox0}
  \showboxbreadth 9999\lefthyphenmin=2\righthyphenmin=3
  \nulldelimiterspace --+.1pt \mathcode`q="3171
  \scriptspace\if00-0.\fi\ifnum'\ifnum10=10 12="\fi
    A 01p\ifdim1,0pt<`^^Abpt\fi\fi % this boils down to -0.01pt
  \overfullrule 5pt \voffset-2pt
  \def\sh{\ifnum\count4>10\else\dimen5=\count4pt
      \advance\dimen5 by 10pt
      \xdef\a{\a\the\count4pt \the\dimen5}
      \advance\count4 by 1 \sh\fi}
  \count4=1 \def\a{} \sh % \def\a{1pt 11pt 2pt 12pt ... 10pt 20pt}
  \let\next=\dump \everyjob{\message{#}}
\else\let\next=\relax\fi
"""

ORIGINAL_TRIPTEST = r"""
% This is a diabolical test file for TeX82. Watch your step.
\immediate\catcode `{ = 1 \endlinechar=13
\catcode `} = 2
\catcode `$ = 3 {\catcode`$13\gdef\dol{$}}
\catcode `& = 4
\let\paR=\par
\let\%=\relax
\outer\xdef\par{\catcode `\% 14}
  % this line should change % from type 5 to type 14
\let\par=\paR \defaulthyphenchar=`- \defaultskewchar=256
\ifx\initex\undefined  \def\initex{} % next lines are skipped if format loaded
  \catcode `# = 6 \catcode `U=\catcode`# % # for parameters
  \catcode `^ = 7 \catcode `| = 8 % ^ for superscripts and | for subscripts
  \catcode `~ = 9 % ~ will be ignored
  \catcode `* = 10 % * will be like a space
  \catcode `E = 12 % E is not a letter
  \catcode`\@ = 15 % @ will be invalid
  \catcode `^^A = 0008 % this is another way to get a subscript
  \catcode `\^^@ = 11 % a strange letter will be allowed
  \catcode `\^^? = \badness % and so will a strange escape delimiter
  \fontdimen12\nullfont=13pt % give the null font more parameters
  \font\trip = trip\relax % see TRIP.PL for details of this font
  ^^?trip  \font\smalltrip=trip scaled 500 % this will be our symbols font
  \global\fontdimen22\smalltrip 7pt % the axis height
  \textfont2=\smalltrip \scriptfont2 \smalltrip \scriptscriptfont2 \smalltrip
  \nonstopmode\lccode256-0\mathchardef\a="8000\def\a{ SCALED 3~2769}
  \font\rip=trip\a % font \rip will be the same as \trip
  \skewchar\rip=`B \countdef\countz % \countz will be \count0
  \def\on{1} \toksdef\tokens=256 \show\errorstopmode
  \showthe\font \showthe\pageshrink \showthe\pagegoal
  \font\bigtr^^@p=trip at20pt\textfont3=\bigtr^^@p % this will be extension font
  \skip200 = 10pt plUs5fil\ifdim\hsize<\hsize\fi lllminus 0 fill
  \setbox200=\vbox{\hrule\vskip\skip200} \wd200-2pt \setbox100=\hbox{A}
  \skipdef\shkip100\shkip -18pt plus\catcode`\}fil minus 10fil
  \advance\shkip by \skip200 \dimen33=3pt \count33=-\dimen33
  \divide\shkip by \count33
  \multiply\shkip by \count33 % so \skip100=-6pt plus 3filll minus 9fil
  \count200 -5 \multiply\count200 by -100 % \count200 is 500
  \count100=1000000 \divide\count100 by \count200 % \count100 is 2000
  \dimen100=,00152587890625in % (100/65536)in = 7227sp
  \multiply\dimen100 by 65536 \divide\dimen100 by 9 % \dimen100 is 803pt
  \lineskip 0pt plus 40pt
  \baselineskip=10pt plus 41pt
  \parskip -0pt plus 42pt minus 8pt
  \splittopskip 1pt plus 43pt
  \splitmaxdepth -2pt \boxmaxdepth 1000pt
  \belowdisplayskip 3pt plus 44pt minus\baselineskip \abovedisplayskip3pt
  \abovedisplayshortskip 1pt plus 45pt minus\dimen100
  \belowdisplayshortskip -\count33sp plus 46pt
  \global\mathchardef\minus"232D % mathbin, family 3, character "2D (-)
  \thinmuskip 1mu plus 2fill minus 3mu
  \medmuskip 2mu minus 3mu
  \thickmuskip -4mu
  \def\gobble#1{} \floatingpenalty 100 \holdinginserts1
  \everypar{A\insert200{\baselineskip400pt\splittopskip\count15pt\hbox{\vadjust
        {\penalty999}}\hbox to -10pt{}}\showthe\pagetotal\showthe\pagegoal
    \advance\count15by1\mark{\the\count15}\splitmaxdepth-1pt
    \paR\gobble} % this aborts every paragraph abruptly
  \def\weird#1{\csname\expandafter\gobble\string#1 \string\csname\endcsname}
  \message{\the\output\weird\one on line \the\inputlineno}
  \hyphenpenalty 88 \exhyphenpenalty 89 \badness
  \clubpenalty 125 \widowpenalty 125 \displaywidowpenalty -125
  \brokenpenalty 37
  \interlinepenalty -125
  \doublehyphendemerits 1000
  \finalhyphendemerits 100000
  \mag 2000 \righthyphenmin=1000000000
  \delimiterfactor 10 \delimitershortfall 190pt
  \showboxbreadth 55 \showboxdepth 9999 \chardef\nul0\def\0{\nul}
  \tracingstats=4 \tracinglostchars=2 \tracingparagraphs\day \tracingpages\year
  \chardef\?=`b \lccode`A=1 \let\^^bbb \hyphenchar\trip=1
  \language-1\hyphenation\relax{b-\?-\char`b -\^^bb-^^62-^^" -t- }\lccode`149
  {\everypar{\parindent\\\looseness-1}\skipdef\\8\language\?\\.01014pt\patterns
  {0111}\emergencystretch9pt\language255\patterns{\the\\} % \patterns{.01015pt}
  {\language256\patterns{0111 \?50AA1b3 *1AcA. bb bb1 0B2B0 b1c}} % *==space
  \pretolerance-1\setbox0=\hbox{11}\setbox0=\hbox{\hbadness100\valign{#\cr
  \hskip-9pt7A\righthyphenmin0\setlanguage\?\unhbox0{*\language`b11\noboundary}
  1Z1pts\patterns{q9q} -\0qq \showlists{\language\?\noboundary111}%
  \hyphenchar\rip=`-\cr}}\patterns{toolate}\showbox0}
  \showboxbreadth 9999\lefthyphenmin=2\righthyphenmin=3
  \nulldelimiterspace --+.1pt \mathcode`q="3171
  \scriptspace\if00-0.\fi\ifnum'\ifnum10=10 12="\fi
    A 01p\ifdim1,0pt<`^^Abpt\fi\fi % this boils down to -0.01pt
  \overfullrule 5pt \voffset-2pt
  \def\sh{\ifnum\count4>10\else\dimen5=\count4pt
      \advance\dimen5 by 10pt
      \xdef\a{\a\the\count4pt \the\dimen5}
      \advance\count4 by 1 \sh\fi}
  \count4=1 \def\a{} \sh % \def\a{1pt 11pt 2pt 12pt ... 10pt 20pt}
  \let\next=\dump \everyjob{\message{#}}
\else\let\next=\relax\fi
\next % if no format was preloaded, this will dump the trip.fmt file and halt
\tracingcommands2\tracingrestores+2\write-1{log file only\the\prevgraf}
\openout-'78terminal \openout10=tr\romannumeral1 \gobble\newcs pos
\write10{} % writing three lines on tripos.tex (the first line is empty)
\write10{\uppercase{\number{\outputpenalty}}} % 0{\outputpenalty} + error
\write10{[\uppercase{\romannumeral-\the\outputpenalty}[} % "mmmmmmmmmm" (-10000)
\vsize 2000pt
\vbadness=1
\topskip 20pt plus 1fil
\penalty -12345 % this will be ignored since the page is still empty
\maxdepth=2pt
\tracingoutput\on
\moveleft20pt\copy200
\moveright20pt\hbox{\vrule depth20pt height-19pt width1pt}
\penalty-10000 % now we'll compute silently for awhile, after default output
\batchmode\output={\tracingcommands0\showthe\outputpenalty
  \showboxbreadth 9999 \showboxdepth 9999 \hoffset1sp
  {\setbox 254=\box255\shipout\ifvbox2\ifhbox254 \error\fi54\copy25\fi4}
  \ifvoid 254\relax\else\error\fi
  }
\setbox255\vbox{}
\dimen200=10000pt
{\output{\dimen 9=\ht200\count5=\dimen9\global\countz=\outputpenalty
    \ifnum\holdinginserts>0\global\holdinginserts0\unvbox255\penalty\countz
    \else\setbox255\copy255 % at end of group, \box255 reverts to former value
    \shipout\hbox{\box100\box200\vsplit 255 to 55pt}
    \unvcopy255\showlists\showthe\insertpenalties\showthe\pageshrink
    \globaldefs1\halign{#\tabskip\lineskip\cr}
    \showboxdepth1\showboxbreadth2\fi
    \message{\topmark:\firstmark:\botmark:\splitfirstmark:\splitbotmark}}
  \insert100{\def\box{\vbox to 267.7pt{}} \vskip0pt plus 1fil
    \baselineskip 0pt \lineskip 0pt minus .4pt
    \box \penalty-101 \box \penalty-100 \box \penalty-1000
    } % since \dimen100=803pt<3*267.7pt, the insertion splits;
  % and the natural height+depth of the split-off part is 267.7pt;
  % now since \count100=2000,
  % this insertion adds about 535.4pt to the current page
  \topskip1pt plus 44pt
  \vbox spread 1000pt{} % beginning of new page
  \insertpenalties=-50\penalty12345
  \cleaders\hbox{\lower2pt\vbox to 17pt{}
    \leaders\hrule\hskip10pt
    \cleaders\hbox{A}\hskip 9pt % the A is 2pt wide
    \leaders\hbox{A}\hskip 9pt
    \xleaders\hbox{A}\hskip 9pt
    \write111{\help} % \write will be ignored in leaders
    }\vskip50pt minus 10pt
  \mark{alpha}
  AAA\everypar=\errhelp % because of previous \everypar, this makes 3 paragraphs
  % and each paragraph consists of A\insert 200{400pt of stuff}\mark{n}
  % but \count200=500 so the inserts are rated 200pt each
  % so the third insertion will be split
  \kern-50pt
  A\hfill\vadjust{\newlinechar128\special{^^80\the\prevdepth}\penalty-5000}%
  \penalty-1000000000 % forces line break in paragraph
  % this is not the end of paragraph
  A\par\insert200{\vskip10000pt\floatingpenalty3}% this insert will be held over
  \pagefilstretch-1pt\showthe\insertpenalties\penalty99999999\showlists
  \showthe\pagefilllstretch\vskip 1000pt\penalty-333\hbox to 23pt{} % output now
  \vsize.pt\global\vsize=16383.99999237060546875pt % page size \approx infinity
  } % now we revert to the former output routine
{\tracingoutput-2\tracingstats1\shipout\hbox{\closeout10\closeout-10}}
\showthe\everypar
\everypar{}\showthe\everypar
\def\showlonglists{{\tracingcommands0\pagefillstretch-1\dimen100
    \showboxbreadth 9999 \showboxdepth 9999 \showlists \pagegoal=10000pt}}
\tracingmacros=1
\def\t12#101001#{-.#1pt} \let\T=\t
\dimendef\varunit=222\varunit=+1,001\ifdim.5\mag>0cc0\fi1pt
\ifdim -0.01001\varunit=\t120100101001001{\relax}\else\error\fi
\countz=-1
\ifodd\count0\advance\countz by -1\fi
\penalty -12345 % output the remaining stuff
\tracingmacros\tracingstats % the next part tests line-break computations
% the two competing ways to set the paragraph have respective demerits
% (30+l)^2+(30+l)^2+a and (51+l)^2+l^2, where a=adjdemerits, l=linepenalty
\adjdemerits=782
\linepenalty=1
\def\1#1{\hbox to#1pt{}}
\valign{\baselineskip20ptplus1pt\global\parfillskip0pt
  \global\global\leftskip4pt
  \rightskip-1pt
  \global\hsize13pt
  \setbox2\12
  \noindent\copy2\hskip2pt plus5pt minus1pt
  \copy2\hskip5pt minus2pt
  \lower2pt\11\hskip3pt % this affects depth of the second line
  \copy2 \hskip2pt plus.5pc
  \box2#\cr
  \noalign{\spacefactor=2000\global\xspaceskip=-1pt}
  \noalign{ \vrule width0pt{ }}
  \cr % set that paragraph with a=782, l=1 (demerits 2704 vs 2705)
  \adjdemerits=784 \cr % increase a, so the second alternative is better
  \linepenalty=2\hbadness=51\cr % increase l by 1, suppress diagnostic typeout
  \noalign{ \spacefactor=1}}\message{\the\spacefactor}
{\hsize1000pt\par\parindent1pt\indent}\leftskip3pt\def\?{\vrule width-2pt
  \hbox spread2pt{}}\noindent\indent\hbox spread2pt{\hskip0pt plus-1bp}%
\discretionary{\?AAAB}{\?B-}{\?/A\kern2pt}\unkern % the widths are 7pt, 4pt, 6pt
\showthe\lastkern\vbox{\hrule width 6pt} \par % should set with nothing overfull
\penalty-22222 % end of demerits test, hyphenation is next
\looseness-10
\uchyph=1
\hsize 100pt
A /A\char`A BBBBCACAC//% that becomes /k[AA]k[BB]k[BB][CA][CA][C/]/,
 % where [] means a ligature and k means a kern.
 % the word "aabbbbcaca" should be hyphenated to "aa1b3b2b2b1c1aca",
 % which becomes {[AA]k-||[AA]k}{B-|[BB]kBk|[BB][BB]}{-||}{C-|A|[CA]}[CA]
 % if I use the notation {x|y|z} for \discretionary{x}{y}{z}.
\vadjust{\uchyph=0\ BBBBBB}% underfull box will show no hyphens
\vadjust{\ \closeout1BBBBBB}{\hyphenchar\trip`C}% this time we get hyphens
\hyphenation{BbB-BbB}\vadjust{\ BBBBBB\kern0ptB}% different hyphens
\hyphenchar\rip`-\vadjust{\def\B{B}\ \pretolerance10000 B\B BBBB} % no hyphens

\hbox{\sfcode`B=1234AB aB }\noindent \scriptscriptfont3 \smalltrip
$$\eqno^{}$\scriptfont3=\rip\fontdimen2\smalltrip=0pt
{\rightskip0pt plus 104pt minus 100fil
  \looseness 5 \spaceskip 4pt plus 2pt minus 1fil
  A\spacefactor32767\discretionary{}{\kern2pt-}{B\kern2pt} C$ \scriptfont2=\trip
  \mathsurround143pt$ C $\mathsurround40pt$$\mathsurround60pt\hbox{$$}$\par}
\uccode`m=`A\font\mumble=mumble\input tripos % "AAAAAAAAAA"+errors
\par\penalty-33333 % end hyphenation, math is next
{\catcode`?=13 \font?xyzzy at0pt\font ? xyzzy scaled1?} % nonexistent
\font\enorm=trip at 2047.999992370605468749999 pt
\font\ip trip at -10pt % through the looking glass
\showthe$
\showthe\font
\message{\fontname\ip}
\rip
\textfont1=\font \scriptfont1=\smalltrip \scriptscriptfont1=\bigtr^^@p % [sick]
\def\symbolpar #1*#2*#3*{\global\fontdimen#1\smalltrip = #3 pt}
{\tracingmacros-1
  \symbolpar8 num1 9.1
  \symbolpar9 num2 9.2
  \symbolpar10 num3  9.3
  \symbolpar11 denom1 3.1
  \symbolpar12 denom2 3.2
  \symbolpar13 sup1 8.1
  \symbolpar"E sup2 8.2
  \symbolpar15 sup3 8.3
  \symbolpar16 sub1 4.1
  \symbolpar17 sub2 4.2
  \symbolpar18 supdrop 0.3
  \symbolpar19 subdrop 0.4
  \symbolpar20 delim1 10
  \symbolpar21 delim2 20
  }
\mathcode`+='20457 % mathbin, family 1, character '57 (/)
\mathcode`=="322D % mathrel, family 2, character "2D (-)
\delcode`["161361 % small (family 1, character "61 (a)), large (3,"61)
\catcode`(=13 \catcode`(=13 \mathcode`y"7320\mathcode`z"8000
\def({\delimiter"4162362 }{\catcode`z=13\global\let z=(}
\parshape 10 \a \chardef\x200
\hangindent- \parshape pt\hangafter-12% \parshape will take precedence
\begingroup
\looseness 2
\rightskip 0pt plus 10fil minus 1sp
\--\--\char-0-A\- % this makes lines 1 to 3
$$\number\the\delcode`\relax\over{{{}}}}\pagestretch=-1\pagetotal\showlists
\begingroup\halign to\the\displaywidth{#&#\crcr\crcr\cr} % makes lines 4--6
\global\count6=\displayindent
\predisplaypenalty=101
\global\postdisplaypenalty-\predisplaysize* \global\setbox=
\eqno % another error (actually causes two error messages and inserts $$)
\looseness-2
$\right\relax\mathchardef\minus="322D % locally \minus is the same as =
\left.A\over A\abovewithdelims.?\right(+\mskip1A\minus=A+\penalty+1000A
\relpenalty-2222
\binoppenalty-3333
\mathsurround.11em$\x % this formula goes on line 7
$$ % here we begin a hairy display that covers lines 8 to 10
\vadjust{\penalty7}\mkern-9mu\the\prevgraf \prevgraf=8 \insert255{\penalty999}
\x\vcenter spread-2pt{} {\mathaccent"32D {A}}|-
^{\raise 2pt\hbox{a}\displaystyle\char`+\textstyle}
\overline{^A A|\minus\mathinner{}^
  {A \mathchar"141 \char`B^^A{\mathaccent"7161
      {\mathop A \mathbin A \mathopen A \mathpunct A\mathclose A \mathrel A
        \global\scriptscriptfont0=\trip
        \mathaccent"161 {\fam13A9\the\scriptscriptfont-1}}}}}
\mathop\char`B^\mathchar"143
\mathop b\nolimits\limits|C
\mathord \radical"161 % missing { will be inserted
  {\textstyle\radical"282382{\left(\scriptscriptstyle\mathop{\underline{
          A\atop\displaystyle A|{A\hfil\over B\nonscript\kern1pt}^=}}
      \nolimits|{\mathop y\nonscript\textstyle\nonscript\mskip9mu minus1fil
        \showthe\lastskip B\abovewithdelims(.2pt\displaylimits}^z
      \discretionary{\showthe\spacefactor-}{\smalltrip A\hss}{\smalltrip A}
      \right[A}}}
\let\penalty=\minus \aftergroup\expandafter
\eqno\aftergroup\relax\scriptstyle\penalty % reader, be alert
(\mathpunct{AA}
|{B\fam1-}^{\hbox{A}}{\above9pt{v\overwithdelims..
    \displaystyle{pq\atopwithdelims((\vrule height 9pt}}
  \show\penalty \showlonglists
  $\expandafter$\csname!\endcsname % end of hairy display, missing } inserted
\parshape=-1 % now the hanging indentation is relevant
\leftskip \parshape pt plus -10fil
\spacefactor1\raise1pt\hbox{\special{\the\hangafter} } \penalty-10000
\showbox0\spacefactor=0
\write10{\the\spacefactor}\par % it's illegal to \write the space factor
} % this fails to match \begingroup
\aftergroup\lccode\aftergroup`\endgroup A`a % this restores \parshape
\mark{\the\spacefactor} % \spacefactor: not in vertical mode
$$\global\count7=\predisplaysize
\mskip18mu minus 18mu \catcode`J=13 \catcode`j=\the\catcode`J \def j{\relax}
\vtop to\displaywidth{\everydisplay{\global}\vbox to -1sp{}\noindent$$
  \count9=\predisplaysize\lowercase{AaJ}$\ifvmode$\fi}\hss
\leqno\mathchardef A\/\left(\over\left(\global\errorcontextlines5$$

\hangindent1pt\par\showthe\hangindent\hangindent 254cm
\parfillskip 0pt plus 100pt \fontdimen6\the\scriptfont2=-19sp
\the\fam % begins a paragraph, but there's no 0 in the font
A \char'202$$\global\count8=\predisplaysize\leqno\kern1009pt$\par
\showlists {\catcode`!13\global\everyhbox{\def!{}}}
\count5=\lastskip % \lastskip=3pt (\belowdisplayskip)
\baselineskip 10pt
{\sfcode`A=500\vfuzz18pt\everyvbox{ }% overfull \vbox won't be shown: 37-8=11+18
  \vbox to 11pt{\hsize 10pt\tolerance 1 A A A A A\clubpenalty10000\par
    \hbadness100\hfuzz 3pt A A A A A\leaders\vrule\hskip5pt\par}
  \message{\the\badness}}
\vbox to 10pt{\hbadness 99\hfuzz1pt\hbox to 0pt{\hskip 10pt minus 9pt}
  \hbadness100\hbox to 10bp{\hskip 0pt plus 10pt}\tracingcommands1
  \if\the\badness\fi\message{\the\badness}}\lineskiplimit-1pt\everyhbox{}
\def\space{ } \dimendef\df=188 \dimen188=1pt
\vbox to 11pt{\tracinglostchars-9 A\/\space\space\ignorespaces\space\space J
  \vskip2pt\moveleft1pt\vbox to10pt{\boxmaxdepth=-1pt\mark{vii}}\vskip3pt
  \unskip\setbox22=\lastbox\showthe\lastskip % \lastskip=-1pt (\baselineskip)
  \unskip\vskip-\lastskip\kern\lastkern\penalty\lastkern\showbox22}
\showbox22\kern3pt\message{\the\lastkern}\unkern
\show\botmark \catcode`;13\def;{\setbox`; }
\lineskiplimit-0.9999 \space\df\space\count9 0
\vbox\space to 11pt{\accent\x\space\accent\space"42 \def\^^M{\  } ; \char'101
  A\     \fontdimen   4 \trip    =    88    pt\     \spaceskip    2    pt      \
  \vskip 10pt minus 10pt}
\penalty-2147483647 % that's the largest value TeX will scan
\penalty-2147483648 % see?
\tabskip 1009.9sp minus .25cc % and now for alignment tests
\let\A=\relax\count1=2{\errhelp{all is lost}\errmessage{}}
\def\d#1\d{#1#1} \looseness-1
\setbox3=\vtop{\vskip-3mm} % this box has a depth of -3mm
\halign spread-12.truedd{&#\span\iftrue\A\span\else\span\fi\span&
  \vbox{\halign to 0pt{\t2\dp3\A\crcr}#A}
  &\hss\tabskip1ex plus7200bp minus 4\wd4\d#\d\cr % \d#\d becomes (erroneous) ##
  \global\let\t=\tabskip \spaceskip=4pt minus 1sp
  \def\A{B}\def\xx{\global\gdef\A{\global\count\count1=####\cr
    \omit\cr\tabskip}}\expandafter\xx\span % please don't ask what this does
  A&\omit\valign to -5pt{#&#\cr A\char`}\span\cr{ }\span\cr}\cr
  \global\edef\A{\uppercase{
      \message{\fontname\smalltrip\the\font\romannumeral1009}\lowercase{vq}} }
  \lccode`Q=`b \span\omit$$\span\A&\show\cr\omit\cr
  \noalign{\global\prevdepth20pt\errmessage{\count2=\the\count2}}
  \omit\mark{a}&\omit\mark{b}\cr} % \count2 was set to -6mm=-1118806sp
\errmessage{\prevdepth=\the\prevdepth}
\penalty-88888 % end alignment test, now miscellaneous error messages
\newlinechar`Y\global\unskip\show^^Y\newlinechar\lastpenalty\unpenalty\unkern
\lastbox\penalty5\message{\the\lastpenalty\the\newlinechar}\textfont16=\relax
\outer\def{}?
\dimen5=-'7777777777sp\showthe\dimen5 % this should be OK
\dimen6=-'40000pt\showthe\dimen6 % this should overflow
\dimen7=.51\dimen5\showthe\dimen7 \multiply\dimen7 2\showthe\dimen7
\a^^@^^@a@ % an undefined control sequence followed by invalid character
{\aftergroup\gobble\aftergroup\c\gdef\b{\c} \def\c{} \b} % \c undefined
\def\b#1\par{}
\outer\gdef\a^^@^^@a#1\par#2{}\tokens{\a^^@^^@a\par!
\long\gdef\l#1{}
\outer\global\long\edef\lo#1#2U3#4#5#6#7#8#8#9#{\relax}
\ifcase 1 \undefined\or\l\par\b{\par % occurrence of \par aborts \b
\b{\l\undefined}\par\else\b{\par}\fi % but not there!
\ifcase\iftrue-1a\else\fi \ifcase0\fi\else\ifcase5\fi\fi
\catcode`^^C = 6 % another parameter symbol
\let\^^C=\halign
\def\^^@^^C{}
\^^C{{\span\ifcase3 \lo#\cr............89{}\cr} % runaway preamble?
\def\a^^C1{\d#1\d\l{#2}\l#1\par\a^^@^^@a#1\par# % runaway in definition; #2 bad
\xdef\a^^C1{\d#1\d\l{#2}\l#1\par\a^^@^^@a#1\par# % runaway in definition; #2 OK!
\T^^?a^^@^^@a\par{\lo\par % runaway in use
\lo\par\par\par  P  \par\par\par\par\par\par89{} \muskip3=-\thickmuskip
\muskipdef\shmip=3 \shmip=5mu plus \muskip3minus.5\shmip \showthe\shmip
{\advance\shmip by \shkip\endlinechar-1
\divide\shmip by \shkip\endlinechar`}
\global\multiply\shmip by 2
\showthe\shmip
\div^^)de\count88
By ^^p \toks1={\a\test}
^\leaders\vrule\mskip\shmip M\leaders\hrule\nonscript\hskip\thinmuskip

{\setbox3\hbox{\vfill\vsplit 3 0pt}
\def\a#2{}
\show A
\show\a^^@^^@a
\show (
\message{\meaning\lo\noexpand\lo}
\show\^^C
\show\batchmode
\show\error
\showthe\output
\showthe\thinmuskip
\showthe\fontdimen1\enorm
\ifx T\span\else\par\if\span\else\else\else\fi\fi
\ifdim72p\iftrue t1i\fi n\fi\fi \message{\jobname\ifx\lo\lo OK}\fi
\hangindent 2pt
{\if 11 \prevgraf=-1\if 0123\error\else\relax\fi\else\error\fi
  \prevgraf1\global\hangafter=2}\showthe\hangafter\showthe\prevgraf
\char'203\showthe\prevgraf$\indent\mark{twain}
\setbox3\hbox{\vrule}&\moveleft\lastbox % can't do that in math mode
\unhbox234\unhcopy3\accent\x\vfill\vfil\vfilneg\vss % \vfill exits, \vss bad
\def\a}{\let\a\xyzzy\csname a\endcsname}
\def\a{ab

  \c}\def\b{ab*\par\c}\let\c\b \def\b{\a\c} \ifx\a\ifx \.
\else\expandafter\ifx\b \ifinner\error\else\relax\fi\else\error\fi\fi
\ifvmode$\ifmmode\hbox tt\ifhmode\hfilneg\else\error\fi}$\fi\fi % missing {
\noalign\omit\endcsname % these are extra
\fontdimen 1000=20\varunit\showthe\fontdimen1000\trip\let\PAR=\par
\gdef\par{\relax\PAR}\expandafter\ifx\csname xyzzy\endcsname\relax \mag=1999

\fi\noindent{\halign to 1truemm\expandafter{\csname#\endcsname#&#&\l{#}\cr
  \global\futurelet\endt\foo&\show\endt&$&&&.}

\hbox{\/\hrule\textfont3=\enorm\prevdepth\advance\xspaceskip by-\xspaceskip
  \spacefactor2000{ }\everymath{\radical"3}\fontdimen2\rip=0pt
  $62{}\delimiterfactor1600\left(Aa\right\delimiter"300$AA\/}
\openin 15 tripos\closein 15\iftrue{\ifeof 15\openin 100 tripos
  \def\loop{\ifeof 0\let\loop=\relax\else{\global\read0to \a}\show\a\fi\loop}
  \catcode`015\catcode`[1\outer\def\uppercase{}\loop}\else\fi
}\def\test#1{\let\test= }\test. \show\test
\def\a#1{\ifcat#1 \message\ifx#1 {\iffalse\fi\the\tokens\fi\fi}}
\pretolerance-1\tokens\toks1\unhbox16\par\everycr{\noalign{\penalty97}}
\the\tokens\ifcase1\or\ifeof\fi\def\stopinput{\error\let\input\die}
\let\lb={\let\rb=}\halign\relax{\span\iffalse}\fi\cr#&\ifnum0=`{\fi\cr\cr}
\let\e\expandafter\def\trap#1{}\def\unbalanced{\halign\lb}\unbalanced#\cr
  \relax\e\e\e\err\e\e\e\endt\e\trap\cr\noexpand\cr}

\expandafter\stopinput\input tripos\endinput\input % one line of tripos
\setbox10=\vbox to8192pt{\hbox{\hbox{\vadjust{A}}}}\vrule\unhbox10\hrule
\output{\showthe\deadcycles\global\advance\countz by1\global\globaldefs-1
  \gdef\local{}\unvbox255\end\rb}\futurelet\dump\maxdeadcycles=3\show\dump
\catcode`q=7 \catcode`\qqM=0 \expandafter\let\csname^^Mendcsname=\^^@\relax
\relax\catcode`\qq1qM=13 \defqqM{\relax}#\begingroup{\showboxdepth=4\showbox10}

\long\def\l#1\l{#1}\immediate\write10{\string\caution \l} % living dangerously
\escapechar`|\tracingoutput0\shipout\vbox{\copy10qq5e^5cbox10}
\setbox9\hbox{\fontdimen8\rip 0pt % \over becomes \atop in \scriptstyle
  \afterassignment\relax\advance\prevdepth\afterassignment\relax\futurelet\x
  \message{\noexpand\l\meaning\l\the\skewchar\ip}\vbox{\hyphenchar\ip-1%
  \-\ BBBBBB\par\hyphenchar\ip`?\-\ BBBBBB}\if$\expandafter\noexpand\dol\fi%
  \expandafter\expandafter\noexpand\undefined\noexpand\expandafter%
  $\begingroup\mathop{\vbox{\vss}}\limits^\mathchoice{}a}{A|{}}{\mathchoice}
  {}{\relax{}{B\over}\endgroup\showlonglists$}\showboxbreadth9\showboxdepth9
\showbox9\PAR{\output{}\penalty-10001\deadcycles=2}\scrollmode%
\hbox{\write-100000{\if01{\else unbal}\fi}\showlists\tracingonline1%
\escapechar127\global\tracingoutput1\global\escapechar256\end
% things not tested:
% interaction (error insertion/deletion, interrupts, \pausing, files not there)
% system-dependent parsing of file names, areas, extensions
% certain error messages, especially fatal ones
% things that can't happen in INITEX
% unusual cases of fixed-point arithmetic
"""
