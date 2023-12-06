El objetivo de esta serie de ejercicios es implementar la representación del inventario de una tienda un tanto especial. Vende todo tipo de objetos mágicos, especialmente pociones, que por desgracia tienden a perder calidad cada día que pasa. 

Un análisis inicial de las necesidades nos permitió identificar este diagrama UML (hemos omitido las relaciones entre clases, que deberá determinar usted mismo) :
[![uml](https://mermaid.ink/img/pako:eNp9UsFOg0AQ_RUyJxqJKdBW5GasTUzsxRoPhst0d8BNYJfsLqa1ab_dpZSKxjoXNvPevnmPnR0wxQlSYCUaMxdYaKwy6bk6drwXQZLjEgvBcNcBbV0N-36uJFePUjCBpZd6XDXrkkYDdkH2TlvBmlIZf-Q9CWMPfeMw4DFV1Rp1D_l4Ogy1Ptxg-p_ixi1aS25U52WAcYErUTTOviX_dGk_TNwrD9Oep0lVrTW5jCurhSwCz8k9k7Ho1M7JA49hKTjyS_9i_n3pL4uOcd8JXEBfsVT6F_Yjw6J7ENPk7k3apA8bRrUVSg5SXSb5XTpnvyJjsOj97yGAinSFgruVOUplYN-pogxSd8yVdrEyyGTLxMaq1VYySK1uKICm5mjptGN9s0YJ6Q42kEbXY1fRNLqJ4tltnEySALaQhtPZdRgl4SSOw_F0MkuSfQCfSjmFMADiwiq9PO1w-zlKvh3xHEtD-y-mD-qw?type=png)](https://mermaid.live/edit#pako:eNp9UsFOg0AQ_RUyJxqJKdBW5GasTUzsxRoPhst0d8BNYJfsLqa1ab_dpZSKxjoXNvPevnmPnR0wxQlSYCUaMxdYaKwy6bk6drwXQZLjEgvBcNcBbV0N-36uJFePUjCBpZd6XDXrkkYDdkH2TlvBmlIZf-Q9CWMPfeMw4DFV1Rp1D_l4Ogy1Ptxg-p_ixi1aS25U52WAcYErUTTOviX_dGk_TNwrD9Oep0lVrTW5jCurhSwCz8k9k7Ho1M7JA49hKTjyS_9i_n3pL4uOcd8JXEBfsVT6F_Yjw6J7ENPk7k3apA8bRrUVSg5SXSb5XTpnvyJjsOj97yGAinSFgruVOUplYN-pogxSd8yVdrEyyGTLxMaq1VYySK1uKICm5mjptGN9s0YJ6Q42kEbXY1fRNLqJ4tltnEySALaQhtPZdRgl4SSOw_F0MkuSfQCfSjmFMADiwiq9PO1w-zlKvh3xHEtD-y-mD-qw)

Con los siguientes requisitos:

* Todos los artículos tienen una variable `int diaRestante` que indica el número de días que tenemos para vender el artículo. `diaRestante` no puede ser inferior a 0, el valor deja de disminuir después.
* El valor de un artículo debe ser el **doble** de su calidad
* Todos los artículos tienen una variable `double calidad` que se utiliza para determinar el valor de venta. `calidad` debe estar comprendido entre 0 y 100 (ambos incluidos). Si el valor no se encuentra entre estos límites, se fija en 0 o 100.
* Al final de cada día, el sistema reduce ambos valores en 1 para cada artículo. Para simular esto, la clase `TiendaMagica` de nuestro sistema tiene un método `diaSiguiente()`.
* Se debe lanzar la excepción `FondoInsuficienteException` para la compra de un artículo sin los fondos necesarios.
* El fondo de la tienda debe actualizarse cuando se compra o vende un objeto (con su valor).

Proporcione las clases y su código para satisfacer estas necesidades. Deben respetarse los nombres de las clases y las firmas de los métodos indicados, pero son libres de crear otros métodos o clases si lo consideran necesario.