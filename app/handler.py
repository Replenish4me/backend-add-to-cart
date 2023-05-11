import boto3
import json
import pymysql
import datetime
import os

def lambda_handler(event, context):
    
    # Leitura dos dados da requisição
    produto_id = event['produto_id']
    quantidade = event['quantidade']
    token = event['token']
    
    # Conexão com o banco de dados
    secretsmanager = boto3.client('secretsmanager')
    response = secretsmanager.get_secret_value(SecretId=f'replenish4me-db-password-{os.environ.get("env", "dev")}')
    db_password = response['SecretString']
    rds = boto3.client('rds')
    response = rds.describe_db_instances(DBInstanceIdentifier=f'replenish4medatabase{os.environ.get("env", "dev")}')
    endpoint = response['DBInstances'][0]['Endpoint']['Address']
    # Conexão com o banco de dados
    with pymysql.connect(
        host=endpoint,
        user='admin',
        password=db_password,
        database='replenish4me'
    ) as conn:
    
        # Verificação da sessão ativa no banco de dados
        with conn.cursor() as cursor:
            sql = "SELECT usuario_id FROM SessoesAtivas WHERE id = %s"
            cursor.execute(sql, (token,))
            result = cursor.fetchone()
            
            if result is None:
                response = {
                    "statusCode": 401,
                    "body": json.dumps({"message": "Sessão inválida"})
                }
                return response
            
            usuario_id = result[0]
            
            # Inserção do produto no carrinho do usuário
            sql = "SELECT id, quantidade FROM CarrinhoCompras WHERE usuario_id = %s AND produto_id = %s"
            cursor.execute(sql, (usuario_id, produto_id))
            result = cursor.fetchone()
            
            if result is None:
                # Inserção do produto no carrinho do usuário
                sql = "INSERT INTO CarrinhoCompras (usuario_id, produto_id, quantidade) VALUES (%s, %s, %s)"
                cursor.execute(sql, (usuario_id, produto_id, quantidade))
                conn.commit()
                
            else:
                # Atualização da quantidade do produto no carrinho do usuário
                carrinho_id = result[0]
                quantidade_atual = result[1]
                
                nova_quantidade = quantidade_atual + quantidade
                
                sql = "UPDATE CarrinhoCompras SET quantidade = %s WHERE id = %s"
                cursor.execute(sql, (nova_quantidade, carrinho_id))
                conn.commit()

    # Retorno da resposta da função
    response = {
        "statusCode": 200,
        "body": json.dumps({"message": "Produto adicionado ao carrinho"})
    }
    return response
