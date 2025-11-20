use crate::{Type, TypeVar};
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct Substitution {
    bindings: HashMap<TypeVar, Type>,
}

impl Substitution {
    pub fn new() -> Self {
        Self {
            bindings: HashMap::new(),
        }
    }

    pub fn bind(&mut self, var: TypeVar, ty: Type) {
        self.bindings.insert(var, ty);
    }

    pub fn lookup(&self, var: TypeVar) -> Option<&Type> {
        self.bindings.get(&var)
    }

    pub fn apply(&self, ty: &Type) -> Type {
        match ty {
            Type::Var(var) => {
                if let Some(bound_ty) = self.lookup(*var) {
                    self.apply(bound_ty)
                } else {
                    ty.clone()
                }
            }
            Type::Function { params, ret } => {
                let new_params = params.iter().map(|p| self.apply(p)).collect();
                let new_ret = Box::new(self.apply(ret));
                Type::Function {
                    params: new_params,
                    ret: new_ret,
                }
            }
            Type::Tuple(types) => {
                let new_types = types.iter().map(|t| self.apply(t)).collect();
                Type::Tuple(new_types)
            }
            _ => ty.clone(),
        }
    }

    pub fn compose(&self, other: &Substitution) -> Substitution {
        let mut result = Substitution::new();

        for (var, ty) in &self.bindings {
            result.bind(*var, other.apply(ty));
        }

        for (var, ty) in &other.bindings {
            if !result.bindings.contains_key(var) {
                result.bind(*var, ty.clone());
            }
        }

        result
    }
}

impl Default for Substitution {
    fn default() -> Self {
        Self::new()
    }
}

pub struct Unification {
    substitution: Substitution,
}

impl Unification {
    pub fn new() -> Self {
        Self {
            substitution: Substitution::new(),
        }
    }

    pub fn unify(&mut self, ty1: &Type, ty2: &Type) -> Result<(), String> {
        let ty1 = self.substitution.apply(ty1);
        let ty2 = self.substitution.apply(ty2);

        match (&ty1, &ty2) {
            (Type::Var(var1), Type::Var(var2)) if var1 == var2 => Ok(()),
            (Type::Var(var), ty) | (ty, Type::Var(var)) => {
                if self.occurs_check(*var, ty) {
                    Err(format!("Occurs check failed: {:?} in {:?}", var, ty))
                } else {
                    self.substitution.bind(*var, ty.clone());
                    Ok(())
                }
            }
            (Type::Int, Type::Int)
            | (Type::Float, Type::Float)
            | (Type::Bool, Type::Bool)
            | (Type::String, Type::String)
            | (Type::Unit, Type::Unit) => Ok(()),
            (
                Type::Function {
                    params: params1,
                    ret: ret1,
                },
                Type::Function {
                    params: params2,
                    ret: ret2,
                },
            ) => {
                if params1.len() != params2.len() {
                    return Err("Function parameter count mismatch".to_string());
                }

                for (p1, p2) in params1.iter().zip(params2.iter()) {
                    self.unify(p1, p2)?;
                }

                self.unify(ret1, ret2)
            }
            (Type::Tuple(types1), Type::Tuple(types2)) => {
                if types1.len() != types2.len() {
                    return Err("Tuple length mismatch".to_string());
                }

                for (t1, t2) in types1.iter().zip(types2.iter()) {
                    self.unify(t1, t2)?;
                }

                Ok(())
            }
            (Type::Custom(name1), Type::Custom(name2)) if name1 == name2 => Ok(()),
            _ => Err(format!("Cannot unify {:?} with {:?}", ty1, ty2)),
        }
    }

    fn occurs_check(&self, var: TypeVar, ty: &Type) -> bool {
        match ty {
            Type::Var(v) if *v == var => true,
            Type::Var(v) => {
                if let Some(bound_ty) = self.substitution.lookup(*v) {
                    self.occurs_check(var, bound_ty)
                } else {
                    false
                }
            }
            Type::Function { params, ret } => {
                params.iter().any(|p| self.occurs_check(var, p))
                    || self.occurs_check(var, ret)
            }
            Type::Tuple(types) => types.iter().any(|t| self.occurs_check(var, t)),
            _ => false,
        }
    }

    pub fn get_substitution(&self) -> &Substitution {
        &self.substitution
    }
}

impl Default for Unification {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_unify_primitives() {
        let mut unif = Unification::new();
        assert!(unif.unify(&Type::Int, &Type::Int).is_ok());
        assert!(unif.unify(&Type::Int, &Type::Bool).is_err());
    }

    #[test]
    fn test_unify_var() {
        let mut unif = Unification::new();
        let var = TypeVar::new(0);
        assert!(unif.unify(&Type::Var(var), &Type::Int).is_ok());
    }

    #[test]
    fn test_substitution() {
        let mut sub = Substitution::new();
        let var = TypeVar::new(0);
        sub.bind(var, Type::Int);
        assert_eq!(sub.apply(&Type::Var(var)), Type::Int);
    }
}
