use ir_gen::IrType;

#[derive(Debug, Clone, PartialEq)]
pub enum CType {
    Int,
    Float,
    Double,
    Char,
    Void,
    Pointer(Box<CType>),
    Function {
        ret: Box<CType>,
        params: Vec<CType>,
    },
    Struct {
        name: String,
        fields: Vec<(String, CType)>,
    },
}

impl CType {
    pub fn from_ir_type(ir_type: &IrType) -> Self {
        match ir_type {
            IrType::Int => CType::Int,
            IrType::Float => CType::Float,
            IrType::Bool => CType::Int,
            IrType::String => CType::Pointer(Box::new(CType::Char)),
            IrType::Void => CType::Void,
            IrType::Pointer(inner) => {
                CType::Pointer(Box::new(CType::from_ir_type(inner)))
            }
            IrType::Function { params, ret } => {
                let c_params = params.iter().map(|p| CType::from_ir_type(p)).collect();
                let c_ret = Box::new(CType::from_ir_type(ret));
                CType::Function {
                    ret: c_ret,
                    params: c_params,
                }
            }
        }
    }

    pub fn to_string(&self) -> String {
        match self {
            CType::Int => "int".to_string(),
            CType::Float => "float".to_string(),
            CType::Double => "double".to_string(),
            CType::Char => "char".to_string(),
            CType::Void => "void".to_string(),
            CType::Pointer(inner) => format!("{}*", inner.to_string()),
            CType::Function { ret, params } => {
                let param_str = params
                    .iter()
                    .map(|p| p.to_string())
                    .collect::<Vec<_>>()
                    .join(", ");
                format!("{} (*)({})", ret.to_string(), param_str)
            }
            CType::Struct { name, .. } => format!("struct {}", name),
        }
    }

    pub fn size(&self) -> usize {
        match self {
            CType::Int | CType::Float => 4,
            CType::Double => 8,
            CType::Char => 1,
            CType::Pointer(_) => 8,
            CType::Void => 0,
            CType::Function { .. } => 8,
            CType::Struct { fields, .. } => fields.iter().map(|(_, t)| t.size()).sum(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ctype_to_string() {
        assert_eq!(CType::Int.to_string(), "int");
        assert_eq!(CType::Void.to_string(), "void");
        assert_eq!(
            CType::Pointer(Box::new(CType::Int)).to_string(),
            "int*"
        );
    }

    #[test]
    fn test_ctype_size() {
        assert_eq!(CType::Int.size(), 4);
        assert_eq!(CType::Char.size(), 1);
        assert_eq!(CType::Pointer(Box::new(CType::Int)).size(), 8);
    }
}
