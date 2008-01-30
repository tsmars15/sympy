
from sympy.core.basic import Basic, S, C
from sympy.core.function import Lambda, Function, Function
from sympy.core.cache import cache_it, cache_it_immutable

class exp(Function):

    nargs = 1

    def fdiff(self, argindex=1):
        if argindex == 1:
            return self
        else:
            raise ArgumentIndexError(self, argindex)

    def inverse(self, argindex=1):
        return log

    @classmethod
    def _eval_apply_subs(self, *args):
        return

    #XXX: investigate why we need the **optionsXXX and remove it
    @classmethod
    def canonize(cls, arg, **optionsXXX):
        arg = Basic.sympify(arg)

        if isinstance(arg, C.Number):
            if arg is S.NaN:
                return S.NaN
            elif arg is S.Zero:
                return S.One
            elif arg is S.One:
                return S.Exp1
            elif arg is S.Infinity:
                return S.Infinity
            elif arg is S.NegativeInfinity:
                return S.Zero
        elif isinstance(arg, log):
            return arg.args[0]
        elif isinstance(arg, C.Mul):
            coeff = arg.as_coefficient(S.Pi*S.ImaginaryUnit)

            if coeff is not None:
                if isinstance(2*coeff, C.Integer):
                    cst_table = {
                        0 : S.One,
                        1 : S.ImaginaryUnit,
                        2 : S.NegativeOne,
                        3 : -S.ImaginaryUnit,
                    }

                    return cst_table[int(2*coeff) % 4]

        if isinstance(arg, C.Add):
            args = arg.args[:]
        else:
            args = [arg]

        included, excluded = [], []

        for arg in args:
            coeff, terms = arg.as_coeff_terms()

            if coeff is S.Infinity:
                excluded.append(coeff**C.Mul(*terms))
            else:
                coeffs, log_term = [coeff], None

                for term in terms:
                    if isinstance(term, log):
                        if log_term is None:
                            log_term = term.args[0]
                        else:
                            log_term = None
                            break
                    elif term.is_comparable:
                        coeffs.append(term)
                    else:
                        break

                if log_term is not None:
                    excluded.append(log_term**C.Mul(*coeffs))
                else:
                    included.append(arg)

        if excluded:
            return C.Mul(*(excluded+[cls(C.Add(*included))]))

    @staticmethod
    @cache_it_immutable
    def taylor_term(n, x, *previous_terms):
        if n<0: return S.Zero
        if n==0: return S.One
        x = Basic.sympify(x)
        if previous_terms:
            p = previous_terms[-1]
            if p is not None:
                return p * x / n
        return x**n/C.Factorial()(n)

    def _eval_expand_complex(self, *args):
        re, im = self.args[0].as_real_imag()
        cos, sin = C.cos(im), C.sin(im)
        return exp(re) * cos + S.ImaginaryUnit * exp(re) * sin

    def _eval_conjugate(self):
        return self.func(self.args[0].conjugate())

    def as_base_exp(self):
        coeff, terms = self.args[0].as_coeff_terms()
        return self.func(C.Mul(*terms)), coeff

    def as_coeff_terms(self, x=None):
        arg = self.args[0]
        if x is not None:
            c,f = arg.as_coeff_factors(x)
            return self.func(c), [self.func(a) for a in f.args]
        if isinstance(arg, C.Add):
            return S.One, [self.func(a) for a in arg.args]
        return S.One,[self]

    def _eval_subs(self, old, new):
        if self==old: return new
        arg = self.args[0]
        o = old
        if isinstance(old, C.Pow): # handle (exp(3*log(x))).subs(x**2, z) -> z**(3/2)
            old = exp(old.exp * log(old.base))
        if isinstance(old, exp):
            b,e = self.as_base_exp()
            bo,eo = old.as_base_exp()
            if b==bo:
                return new ** (e/eo) # exp(2/3*x*3).subs(exp(3*x),y) -> y**(2/3)
            if isinstance(arg, C.Add): # exp(2*x+a).subs(exp(3*x),y) -> y**(2/3) * exp(a)
                # exp(exp(x) + exp(x**2)).subs(exp(exp(x)), w) -> w * exp(exp(x**2))
                oarg = old.args[0]
                new_l = []
                old_al = []
                coeff2,terms2 = oarg.as_coeff_terms()
                for a in arg.args:
                    a = a.subs(old, new)
                    coeff1,terms1 = a.as_coeff_terms()
                    if terms1==terms2:
                        new_l.append(new**(coeff1/coeff2))
                    else:
                        old_al.append(a.subs(old, new))
                if new_l:
                    new_l.append(self.func(C.Add(*old_al)))
                    r = C.Mul(*new_l)
                    return r
        old = o
        return Function._eval_subs(self, old, new)

    def _eval_is_real(self):
        return self.args[0].is_real

    def _eval_is_positive(self):
        if self.args[0].is_real:
            return True

    def _eval_is_bounded(self):
        arg = self.args[0]
        if arg.is_unbounded:
            if arg.is_negative: return True
            if arg.is_positive: return False
        if arg.is_bounded:
            return True
        if arg.is_real:
            return False
    def _eval_is_zero(self):
        return (self.args[0] is S.NegativeInfinity)

    def _eval_power(b, e):
        """exp(b[0])**e -> exp(b[0]*e)"""
        return exp(b.args[0] * e)

    def _eval_oseries(self, order):
        #XXX quick hack, to pass the tests:
        #print "XX", self, order
        #w = C.Symbol("w")
        #if self[0] == (1 + w)*(-log(w) + log(C.sin(2*w))):
        #    if order == C.Order(w**3,w):
        #        return self
        #    else:
        #        return self
        #if self[0] == w*log(2*C.cos(w)*C.sin(w)) - w*log(w):
        #    if order == C.Order(w**3,w):
        #        return 1 + w*log(2) + w**2*log(2)**2/2
        #    else:
        #        return S.One
        #if self[0] == (1 + w)*log(1/w*C.sin(2*w)):
        #    return exp((1 + w)*(-log(w) + log(C.sin(2*w))))
        #print "XX2...."
        #Example: 
        #  self       = exp(log(1 + x)/x)
        #  order      = O(x**2)

        arg = self.args[0]
        #  arg        = log(1 + x)/x
        x = order.symbols[0]
        #  x          = x
        if not C.Order(1,x).contains(arg): # singularity
            arg0 = arg.as_leading_term(x)
            d = (arg-arg0).limit(x, S.Zero)
            if d is not S.Zero:
                return exp(arg)
        else:
            #  arg = log(1+x)/x   ~ O(1)
            arg0 = arg.limit(x, S.Zero)
            #  arg0 = 1
        o = order * exp(-arg0)
        #  o = O(x**2) * exp(-1)
        return self._compute_oseries(arg-arg0, o, exp.taylor_term, exp) * exp(arg0)

    def _eval_as_leading_term(self, x):
        arg = self.args[0]
        if isinstance(arg, C.Add):
            return C.Mul(*[exp(f).as_leading_term(x) for f in arg.args])
        arg = self.args[0].as_leading_term(x)
        if C.Order(1,x).contains(arg):
            return S.One
        return exp(arg)

    def _eval_expand_basic(self, *args):
        arg = self.args[0].expand()
        if isinstance(arg, C.Add):
            expr = 1
            for x in arg.args:
                expr *= self.func(x).expand()
            return expr
        return self.func(arg)

    def _sage_(self):
        import sage.all as sage
        return sage.exp(self[0]._sage_())

class log(Function):

    nargs = (1,2)
    is_comparable = True

    def fdiff(self, argindex=1):
        if argindex == 1:
            return 1/self.args[0]
            s = C.Symbol('x', dummy=True)
            return Lambda(s**(-1), s)
        else:
            raise ArgumentIndexError(self, argindex)

    def inverse(self, argindex=1):
        return exp

    @classmethod
    def _eval_apply_subs(self, *args):
        return

    #XXX: why is the fixme parameter needed here?
    @classmethod
    def canonize(cls, arg, base=None, **fixme):
        if base is not None:
            base = Basic.sympify(base)

            if base is not S.Exp1:
                return cls(arg)/cls(base)

        arg = Basic.sympify(arg)

        if isinstance(arg, C.Number):
            if arg is S.Zero:
                return S.NegativeInfinity
            elif arg is S.One:
                return S.Zero
            elif arg is S.Infinity:
                return S.Infinity
            elif arg is S.NegativeInfinity:
                return S.Infinity
            elif arg is S.NaN:
                return S.NaN
            elif arg.is_negative:
                return S.Pi * S.ImaginaryUnit + cls(-arg)
        elif arg is S.Exp1:
            return S.One
        #this doesn't work due to caching: :(
        #elif isinstance(arg, exp) and arg[0].is_real:
        #using this one instead:
        elif isinstance(arg, exp):
            return arg.args[0]
        #this shouldn't happen automatically (see the issue 252):
        #elif isinstance(arg, C.Pow):
        #    if isinstance(arg.exp, C.Number) or \
        #       isinstance(arg.exp, C.NumberSymbol) or arg.exp.is_number:
        #        return arg.exp * self(arg.base)
        #elif isinstance(arg, C.Mul) and arg.is_real:
        #    return C.Add(*[self(a) for a in arg])
        elif not isinstance(arg, C.Add):
            coeff = arg.as_coefficient(S.ImaginaryUnit)

            if coeff is not None:
                if coeff is S.Infinity:
                    return S.Infinity
                elif coeff is S.NegativeInfinity:
                    return S.Infinity
                elif isinstance(coeff, C.Rational):
                    if coeff.is_nonnegative:
                        return S.Pi * S.ImaginaryUnit * S.Half + cls(coeff)
                    else:
                        return -S.Pi * S.ImaginaryUnit * S.Half + cls(-coeff)

    def as_base_exp(self):
        return self, S.One
        #why is this here:?
        return exp, S.NegativeOne

    def _calc_apply_positive(self, x):
        if x.is_positive and x.is_unbounded: return True

    def _calc_apply_unbounded(self, x):
        return x.is_unbounded

    @staticmethod
    @cache_it_immutable
    def taylor_term(n, x, *previous_terms): # of log(1+x)
        if n<0: return S.Zero
        x = Basic.sympify(x)
        if n==0: return x
        if previous_terms:
            p = previous_terms[-1]
            if p is not None:
                return (-n) * p * x / (n+1)
        return (1-2*(n%2)) * x**(n+1)/(n+1)

    def _eval_expand_complex(self, *args):
        re, im = self.args[0].as_real_imag()
        return log(re**S.Half + im**S.Half) + \
               S.ImaginaryUnit * C.arg(self.args[0])

    def _eval_is_real(self):
        return self.args[0].is_positive

    def _eval_is_bounded(self):
        arg = self.args[0]
        if arg.is_infinitesimal:
            return False
        return arg.is_bounded

    def _eval_is_positive(self):
        arg = self.args[0]
        if arg.is_positive:
            if arg.is_unbounded: return True
            if arg.is_infinitesimal: return False
            if isinstance(arg, C.Number):
                return arg>1

    def _eval_is_zero(self):
        # XXX This is not quite useless. Try evaluating log(0.5).is_negative
        #     without it. There's probably a nicer way though.
        return (self.args[0] is S.One)

    def as_numer_denom(self):
        n, d = self.args[0].as_numer_denom()
        if d is S.One:
            return self.func(n), d
        return (self.func(n) - self.func(d)).as_numer_denom()

    # similar code must be added to other functions with have singularites
    # in their domains eg. cot(), tan() ...
    # the trick is to factor out the singularity and leave it as is, and expand
    # the rest, that can be expanded.
    def _eval_oseries(self, order):
        arg = self.args[0]
        x = order.symbols[0]
        ln = C.log
        use_lt = not C.Order(1,x).contains(arg)
        if not use_lt:
            arg0 = arg.limit(x, 0)
            use_lt = (arg0 is S.Zero)
        if use_lt: # singularity, #example: self = log(sin(x))
            # arg = (arg / lt) * lt    
            lt = arg.as_leading_term(x) # arg = sin(x); lt = x
            a = (arg/lt).expand() # a = sin(x)/x 
            #the idea is to recursively call ln(a).series(), but the problem
            #is, that ln(sin(x)/x) gets "simplified" to -log(x)+ln(sin(x)) and
            #an infinite recursion occurs, see also the issue 252. 
            return ln(lt) + ln(a).oseries(order)
        # arg -> arg0 + (arg - arg0) -> arg0 * (1 + (arg/arg0 - 1))
        z = (arg/arg0 - 1)
        return self._compute_oseries(z, order, ln.taylor_term, lambda z: ln(1+z)) + ln(arg0)

    def _eval_as_leading_term(self, x):
        arg = self.args[0].as_leading_term(x)
        if arg is S.One:
            return (self.args[0] - 1).as_leading_term(x)
        return self.func(arg)

    def _eval_expand_basic(self, *args):
        arg = self.args[0]
        if isinstance(arg, C.Mul) and arg.is_real:
            expr = 0
            for x in arg.args:
                expr += self.func(x).expand()
            return expr
        elif isinstance(arg, C.Pow):
            if isinstance(arg.exp, C.Number) or \
               isinstance(arg.exp, C.NumberSymbol):
                return arg.exp * self.func(arg.base).expand()
        return self

    #this is a lot faster:
    @classmethod
    def _eval_apply_evalf(cls, arg):
        arg = arg.evalf()
        if arg.is_number:
            import math
            from sympy import Real
            return Real(math.log(arg))

    def _sage_(self):
        import sage.all as sage
        return sage.log(self[0]._sage_())

# MrvLog is used by limit.py
class MrvLog(log):

    def subs(self, old, new):
        old = Basic.sympify(old)
        if old==self.func:
            arg = self.args[0]
            new = Basic.sympify(new)
            return new(arg.subs(old, new))
        return self
